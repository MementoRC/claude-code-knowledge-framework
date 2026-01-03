# \!/usr/bin/env python3
"""
Orchestrated Quality Tools Workflow
===================================

This script demonstrates the systematic application of automated quality tools
with effectiveness tracking and manual intervention identification.
"""

import subprocess
from typing import Any


class QualityOrchestrator:
    """Orchestrates multiple quality tools with effectiveness tracking."""

    def __init__(self):
        self.initial_state = None
        self.tool_results = []

    def run_command(self, cmd: str) -> tuple[str, str, int]:
        """Execute command and return results."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1

    def analyze_violations(self) -> dict[str, int]:
        """Get current violation counts."""
        stdout, _, _ = self.run_command(
            "pixi run -e quality ruff check src/ tests/ --statistics"
        )

        violations = {}
        if stdout:
            for line in stdout.strip().split("\n"):
                if "\t" in line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        count = int(parts[0].strip())
                        code = parts[1].strip()
                        violations[code] = count
        return violations

    def apply_ruff_format(self) -> dict[str, Any]:
        """Apply ruff formatting."""
        print("🔧 Applying ruff format...")
        stdout, stderr, returncode = self.run_command(
            "pixi run -e quality ruff format src/ tests/"
        )

        result = {
            "tool": "ruff_format",
            "success": returncode == 0,
            "output": stdout + stderr,
            "effectiveness": "high" if returncode == 0 else "failed",
        }

        if "left unchanged" in stdout:
            result["files_changed"] = 0
            result["status"] = "already_compliant"
        else:
            # Count changed files
            result["files_changed"] = stdout.count("reformatted")
            result["status"] = "changes_applied"

        return result

    def apply_ruff_fix(self) -> dict[str, Any]:
        """Apply ruff auto-fixes."""
        print("🔧 Applying ruff --fix...")
        before_violations = self.analyze_violations()

        stdout, stderr, returncode = self.run_command(
            "pixi run -e quality ruff check --fix src/ tests/"
        )

        after_violations = self.analyze_violations()

        # Calculate fixes applied
        fixes_applied = {}
        for code, before_count in before_violations.items():
            after_count = after_violations.get(code, 0)
            if before_count > after_count:
                fixes_applied[code] = before_count - after_count

        return {
            "tool": "ruff_fix",
            "success": len(fixes_applied) > 0,
            "fixes_applied": fixes_applied,
            "total_fixes": sum(fixes_applied.values()),
            "before_total": sum(before_violations.values()),
            "after_total": sum(after_violations.values()),
            "effectiveness": "high" if fixes_applied else "limited",
        }

    def identify_manual_fixes(self) -> dict[str, Any]:
        """Identify violations requiring manual intervention."""
        violations = self.analyze_violations()

        manual_fix_patterns = {
            "B904": {
                "description": "Exception chaining required",
                "pattern": 'Add "from e" to raise statements',
                "example": "raise HTTPException(...) from e",
            },
            "B017": {
                "description": "Specific exception types needed",
                "pattern": "Replace Exception with specific types",
                "example": "pytest.raises(ValueError) instead of Exception",
            },
            "B019": {
                "description": "Cached method memory leaks",
                "pattern": "Use functools.cached_property or refactor",
                "example": "@cached_property instead of @lru_cache",
            },
            "UP035": {
                "description": "Deprecated typing imports",
                "pattern": "Replace typing.Dict with dict",
                "example": "dict[str, int] instead of Dict[str, int]",
            },
        }

        manual_fixes = {}
        for code, count in violations.items():
            if code in manual_fix_patterns:
                manual_fixes[code] = {"count": count, **manual_fix_patterns[code]}

        return {
            "manual_fixes": manual_fixes,
            "total_manual": sum(info["count"] for info in manual_fixes.values()),
            "automation_blocked": len(manual_fixes) > 0,
        }

    def generate_report(self) -> None:
        """Generate comprehensive orchestration report."""
        print("\n" + "=" * 60)
        print("QUALITY TOOLS ORCHESTRATION REPORT")
        print("=" * 60)

        # Initial state
        if not self.initial_state:
            self.initial_state = self.analyze_violations()

        initial_total = sum(self.initial_state.values())
        print(f"\n📊 INITIAL STATE: {initial_total} violations")

        # Apply tools in sequence
        format_result = self.apply_ruff_format()
        fix_result = self.apply_ruff_fix()
        manual_analysis = self.identify_manual_fixes()

        self.tool_results = [format_result, fix_result]

        # Final state
        final_violations = self.analyze_violations()
        final_total = sum(final_violations.values())

        print(f"\n📊 FINAL STATE: {final_total} violations")
        print(f"📈 IMPROVEMENT: {initial_total - final_total} violations resolved")

        # Tool effectiveness
        print("\n🔧 TOOL EFFECTIVENESS:")
        print(f"   ruff format: {format_result['effectiveness']}")
        print(f"   ruff --fix: {fix_result['effectiveness']}")

        if fix_result["total_fixes"] > 0:
            print(f"   Fixes applied: {fix_result['fixes_applied']}")

        # Manual intervention needed
        print("\n⚠️  MANUAL INTERVENTION REQUIRED:")
        print(f"   Total violations: {manual_analysis['total_manual']}")

        for code, info in manual_analysis["manual_fixes"].items():
            print(f"\n   {code} ({info['count']} violations):")
            print(f"   • {info['description']}")
            print(f"   • Pattern: {info['pattern']}")
            print(f"   • Example: {info['example']}")

        # Success rate
        automation_rate = (
            (initial_total - manual_analysis["total_manual"]) / initial_total
        ) * 100
        print(f"\n📊 AUTOMATION SUCCESS RATE: {automation_rate:.1f}%")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Continue with manual fixes for B904, B017, B019")
        print("   2. Investigate UP035 auto-fix configuration")
        print("   3. Consider pre-commit hooks for formatting")
        print("   4. Regular quality orchestration in CI/CD")


def main():
    """Main orchestration workflow."""
    orchestrator = QualityOrchestrator()
    orchestrator.generate_report()


if __name__ == "__main__":
    main()
