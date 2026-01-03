#!/usr/bin/env python3
"""
Quality Tools Orchestration Effectiveness Report
===============================================

This script tracks the effectiveness of automated quality tools
and provides insights into which tools are most effective for
different types of violations.
"""

import subprocess
from datetime import datetime
from typing import Any


def run_command(cmd: str) -> tuple[str, str, int]:
    """Run command and return output, handling errors gracefully."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def analyze_current_state() -> dict[str, Any]:
    """Analyze current quality violations."""
    print("=== CURRENT QUALITY STATE ANALYSIS ===\n")

    # Get violations with statistics
    stdout, stderr, returncode = run_command(
        "pixi run -e quality ruff check src/ tests/ --statistics"
    )

    violations = {}
    if stdout:
        lines = stdout.strip().split("\n")
        for line in lines:
            if "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    count = int(parts[0].strip())
                    code = parts[1].strip()
                    violations[code] = count

    # Get format violations
    stdout_fmt, stderr_fmt, returncode_fmt = run_command(
        "pixi run -e quality ruff format --check src/ tests/"
    )

    format_issues = 0
    if returncode_fmt != 0:
        lines = (stdout_fmt + stderr_fmt).split("\n")
        format_files = [line for line in lines if "Would reformat:" in line]
        format_issues = len(format_files)

    return {
        "violations": violations,
        "format_issues": format_issues,
        "total_violations": sum(violations.values()),
        "timestamp": datetime.now().isoformat(),
    }


def categorize_by_tool_effectiveness() -> dict[str, Any]:
    """Categorize violations by which tools can fix them."""

    tool_categories = {
        "ruff_format": {
            "description": "Code formatting (ruff format)",
            "effectiveness": "High",
            "auto_fixable": True,
            "codes": ["E111", "E114", "E117", "W291", "W292", "W293", "W391"],
        },
        "ruff_fix_imports": {
            "description": "Import sorting and organization (ruff --fix)",
            "effectiveness": "High",
            "auto_fixable": True,
            "codes": ["I001", "I002", "I003", "I004", "I005"],
        },
        "ruff_fix_modernization": {
            "description": "Python syntax modernization (ruff --fix)",
            "effectiveness": "High",
            "auto_fixable": True,
            "codes": ["UP035"],  # Should be fixable but having issues
        },
        "ruff_fix_comprehensions": {
            "description": "List/dict comprehension improvements (ruff --fix)",
            "effectiveness": "High",
            "auto_fixable": True,
            "codes": ["C400", "C401", "C402", "C403", "C404", "C405", "C406"],
        },
        "manual_fixes_required": {
            "description": "Requires manual intervention",
            "effectiveness": "Manual",
            "auto_fixable": False,
            "codes": ["B904", "B017", "B019"],
        },
    }

    return tool_categories


def generate_effectiveness_report() -> None:
    """Generate comprehensive effectiveness report."""

    current_state = analyze_current_state()
    tool_categories = categorize_by_tool_effectiveness()

    print("QUALITY TOOLS ORCHESTRATION REPORT")
    print("=" * 50)
    print(f"Generated: {current_state['timestamp']}")
    print()

    print("CURRENT VIOLATION SUMMARY")
    print("-" * 30)
    print(f"Total violations: {current_state['total_violations']}")
    print(f"Format issues: {current_state['format_issues']}")
    print()

    # Calculate auto-fixable vs manual
    auto_fixable_count = 0
    manual_count = 0

    for violation_code, count in current_state["violations"].items():
        is_auto_fixable = False
        for tool_name, tool_info in tool_categories.items():
            if violation_code in tool_info["codes"] and tool_info["auto_fixable"]:
                is_auto_fixable = True
                break

        if is_auto_fixable:
            auto_fixable_count += count
        else:
            manual_count += count

    total_issues = current_state["total_violations"] + current_state["format_issues"]
    auto_fixable_total = auto_fixable_count + current_state["format_issues"]

    print("TOOL EFFECTIVENESS ANALYSIS")
    print("-" * 30)
    print(
        f"Auto-fixable issues: {auto_fixable_total}/{total_issues} ({auto_fixable_total / total_issues * 100:.1f}%)"
    )
    print(
        f"Manual fixes required: {manual_count}/{total_issues} ({manual_count / total_issues * 100:.1f}%)"
    )
    print()

    print("TOOL-SPECIFIC EFFECTIVENESS")
    print("-" * 30)

    for tool_name, tool_info in tool_categories.items():
        relevant_violations = sum(
            current_state["violations"].get(code, 0) for code in tool_info["codes"]
        )

        if tool_name == "ruff_format":
            relevant_violations += current_state["format_issues"]

        print(f"\n{tool_info['description']}:")
        print(f"  Effectiveness: {tool_info['effectiveness']}")
        print(f"  Auto-fixable: {tool_info['auto_fixable']}")
        print(f"  Current violations: {relevant_violations}")

        if relevant_violations > 0:
            if tool_info["auto_fixable"]:
                print("  💡 Recommendation: Run automated fix")
            else:
                print("  ⚠️  Recommendation: Manual review required")

    print("\nRECOMMENDEd AUTOMATION SEQUENCE")
    print("-" * 30)
    print("1. ruff format src/ tests/          # Fix formatting")
    print("2. ruff check --fix src/ tests/     # Fix auto-correctable")
    print("3. Manual review for B904, B017     # Exception handling")
    print("4. Manual review for B019           # Cached methods")
    print()

    print("ISSUES REQUIRING INVESTIGATION")
    print("-" * 30)
    up035_count = current_state["violations"].get("UP035", 0)
    if up035_count > 0:
        print(
            f"⚠️  UP035 violations ({up035_count}): Should be auto-fixable but not applying"
        )
        print("   Investigation needed: Python version compatibility or ruff config")

    b904_count = current_state["violations"].get("B904", 0)
    if b904_count > 0:
        print(f"🔧 B904 violations ({b904_count}): Add 'from e' to raise statements")
        print("   Pattern: raise Exception(...) -> raise Exception(...) from e")


if __name__ == "__main__":
    generate_effectiveness_report()
