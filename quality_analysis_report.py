#!/usr/bin/env python3
"""
Quality Violations Analysis for Automated Fix Opportunities
===========================================================

This script analyzes current quality violations and categorizes them by
automated fix potential using tools like ruff --fix, black, isort, autopep8.
"""

import json
import subprocess
from collections import defaultdict


def run_command(cmd):
    """Run command and return output, handling errors gracefully."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def analyze_ruff_violations():
    """Analyze ruff violations for automated fix potential."""
    print("=== RUFF VIOLATION ANALYSIS ===\n")

    # Get all ruff violations in JSON format
    stdout, stderr, returncode = run_command(
        "pixi run -e quality ruff check src/ tests/ --output-format=json"
    )

    if returncode != 0 and not stdout:
        print(f"Failed to run ruff check: {stderr}")
        return {}

    try:
        violations = json.loads(stdout) if stdout else []
    except json.JSONDecodeError:
        print(f"Failed to parse ruff output: {stdout[:200]}...")
        return {}

    # Auto-fixable violation codes (ruff --fix supported)
    auto_fixable_codes = {
        # Import sorting (isort)
        "I001",
        "I002",
        "I003",
        "I004",
        "I005",
        # pyupgrade - Python syntax modernization
        "UP001",
        "UP003",
        "UP004",
        "UP005",
        "UP006",
        "UP007",
        "UP008",
        "UP009",
        "UP010",
        "UP011",
        "UP012",
        "UP013",
        "UP014",
        "UP015",
        "UP017",
        "UP018",
        "UP019",
        "UP020",
        "UP021",
        "UP022",
        "UP023",
        "UP024",
        "UP025",
        "UP026",
        "UP027",
        "UP028",
        "UP029",
        "UP030",
        "UP031",
        "UP032",
        "UP033",
        "UP034",
        "UP035",
        "UP036",
        "UP037",
        "UP038",
        "UP039",
        "UP040",
        "UP041",
        "UP042",
        # flake8-comprehensions
        "C400",
        "C401",
        "C402",
        "C403",
        "C404",
        "C405",
        "C406",
        "C407",
        "C408",
        "C409",
        "C410",
        "C411",
        "C413",
        "C414",
        "C415",
        "C416",
        "C417",
        "C418",
        "C419",
        # Whitespace and formatting (pycodestyle)
        "W291",
        "W292",
        "W293",
        "W391",
        "E111",
        "E114",
        "E117",
        "E201",
        "E202",
        "E203",
        "E211",
        "E221",
        "E222",
        "E223",
        "E224",
        "E225",
        "E226",
        "E227",
        "E228",
        "E231",
        "E241",
        "E242",
        "E251",
        "E261",
        "E262",
        "E265",
        "E266",
        "E271",
        "E272",
        "E273",
        "E274",
        "E275",
        # Some pyflakes fixes
        "F401",
        "F404",
        "F541",
        "F811",
        # Some flake8-bugbear fixes
        "B006",
        "B007",
        "B014",
        "B018",
        "B023",
        "B034",
    }

    # Categorize violations
    violation_counts = defaultdict(int)
    fixable_counts = defaultdict(int)
    file_violations = defaultdict(list)

    for violation in violations:
        code = violation["code"]
        filename = violation["filename"]

        violation_counts[code] += 1
        file_violations[filename].append(violation)

        if code in auto_fixable_codes:
            fixable_counts[code] += 1

    total_violations = sum(violation_counts.values())
    total_fixable = sum(fixable_counts.values())

    print("SUMMARY")
    print(f"Total violations: {total_violations}")
    print(f"Auto-fixable violations: {total_fixable}")
    if total_violations > 0:
        print(f"Auto-fixable percentage: {total_fixable/total_violations*100:.1f}%\n")

    print("TOP AUTO-FIXABLE VIOLATIONS")
    auto_fixable_sorted = [
        (code, count)
        for code, count in violation_counts.items()
        if code in auto_fixable_codes
    ]
    auto_fixable_sorted.sort(key=lambda x: x[1], reverse=True)

    for code, count in auto_fixable_sorted[:10]:
        print(f"  {code}: {count} violations (100% auto-fixable)")

    print("\nTOP MANUAL-FIX-REQUIRED VIOLATIONS")
    manual_fix_sorted = [
        (code, count)
        for code, count in violation_counts.items()
        if code not in auto_fixable_codes
    ]
    manual_fix_sorted.sort(key=lambda x: x[1], reverse=True)

    for code, count in manual_fix_sorted[:10]:
        print(f"  {code}: {count} violations (requires manual fix)")

    print("\nFILES WITH MOST VIOLATIONS")
    file_counts = [(f, len(viols)) for f, viols in file_violations.items()]
    file_counts.sort(key=lambda x: x[1], reverse=True)

    for filename, count in file_counts[:10]:
        auto_fix_count = sum(
            1 for v in file_violations[filename] if v["code"] in auto_fixable_codes
        )
        manual_count = count - auto_fix_count
        short_name = filename.split("/")[-1]
        print(
            f"  {short_name}: {count} total ({auto_fix_count} auto-fixable, {manual_count} manual)"
        )

    return {
        "total_violations": total_violations,
        "auto_fixable": total_fixable,
        "violation_counts": dict(violation_counts),
        "auto_fixable_codes": auto_fixable_codes,
        "file_violations": dict(file_violations),
    }


def analyze_formatting_violations():
    """Analyze formatting violations fixable by ruff format (black-compatible)."""
    print("\n=== FORMATTING ANALYSIS ===\n")

    stdout, stderr, returncode = run_command(
        "pixi run -e quality ruff format --check src/ tests/"
    )

    if returncode == 0:
        print("No formatting violations found")
        return {"files_needing_format": 0}

    lines = stdout.split("\n") + stderr.split("\n")
    files_to_reformat = []

    for line in lines:
        if "Would reformat:" in line:
            filename = line.split("Would reformat: ")[-1].strip()
            files_to_reformat.append(filename)

    print("FORMATTING VIOLATIONS")
    print(f"Files needing reformatting: {len(files_to_reformat)}")
    print("100% auto-fixable with 'ruff format'\n")

    if files_to_reformat:
        print("Files to reformat:")
        for filename in files_to_reformat[:10]:  # Show first 10
            short_name = filename.split("/")[-1]
            print(f"  {short_name}")
        if len(files_to_reformat) > 10:
            print(f"  ... and {len(files_to_reformat) - 10} more")

    return {"files_needing_format": len(files_to_reformat)}


def main():
    """Main analysis function."""
    print("QUALITY VIOLATIONS ANALYSIS FOR AUTOMATED FIX OPPORTUNITIES")
    print("=" * 60)
    print("")

    # Run analyses
    ruff_analysis = analyze_ruff_violations()
    format_analysis = analyze_formatting_violations()

    # Generate summary
    print("\n=== OVERALL SUMMARY ===\n")

    total_issues = ruff_analysis.get("total_violations", 0) + format_analysis.get(
        "files_needing_format", 0
    )

    auto_fixable_issues = ruff_analysis.get("auto_fixable", 0) + format_analysis.get(
        "files_needing_format", 0
    )

    print("QUALITY METRICS")
    print(f"Total quality issues: {total_issues}")
    print(f"Auto-fixable issues: {auto_fixable_issues}")
    if total_issues > 0:
        print(f"Overall auto-fix ratio: {auto_fixable_issues/total_issues*100:.1f}%")

    print("\nAUTOMATED FIX RECOMMENDATIONS")
    print("1. Format code:")
    print("   pixi run -e quality ruff format src/ tests/")
    print("")
    print("2. Fix auto-correctable lint violations:")
    print("   pixi run -e quality ruff check --fix src/ tests/")
    print("")
    print("3. Emergency fix script (combines above):")
    print("   pixi run emergency-fix")
    print("")

    print("MANUAL FIXES REQUIRED")
    print(
        "1. Exception handling (B904): Add 'from err' or 'from None' to raise statements"
    )
    print(
        "2. Test assertions (B017): Replace 'Exception' with specific exception types"
    )
    print("3. Type annotations: Add missing type hints for mypy compliance")


if __name__ == "__main__":
    main()
