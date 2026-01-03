"""
UCKN Quality Metrics Dashboard

- Summarizes test results and coverage
- Enforces quality gates
- Generates reports for CI and local use
"""

import argparse
import json
import os
import sys
from typing import Any

from tests.quality_metrics.coverage_analysis import (
    extract_coverage_metrics,
    load_coverage_json,
    print_coverage_trend,
)

PYTEST_JSON = os.environ.get("UCKN_PYTEST_JSON", "pytest-report.json")
COVERAGE_JSON = os.environ.get("UCKN_COVERAGE_JSON", "coverage.json")
DEFAULT_FAIL_UNDER = 90


def load_pytest_json(path: str = PYTEST_JSON) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def summarize_pytest_results(pytest_json: dict[str, Any]) -> dict[str, Any]:
    summary = pytest_json.get("summary", {})
    return {
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "skipped": summary.get("skipped", 0),
        "errors": summary.get("errors", 0),
        "duration": summary.get("duration", 0.0),
        "total": sum(
            summary.get(k, 0) for k in ["passed", "failed", "skipped", "errors"]
        ),
    }


def print_summary(pytest_metrics: dict[str, Any], coverage_metrics: dict[str, Any]):
    print("==== UCKN Quality Metrics Summary ====")
    print(
        f"Tests: {pytest_metrics['total']} | Passed: {pytest_metrics['passed']} | Failed: {pytest_metrics['failed']} | Skipped: {pytest_metrics['skipped']} | Errors: {pytest_metrics['errors']}"
    )
    print(f"Test Duration: {pytest_metrics['duration']:.2f}s")
    print(
        f"Coverage: {coverage_metrics['percent_covered']}% lines, {coverage_metrics.get('percent_branches_covered', 'N/A')}% branches"
    )
    print(
        f"Statements: {coverage_metrics['num_statements']} | Covered: {coverage_metrics['covered_lines']} | Missing: {coverage_metrics['missing_lines']}"
    )
    print("======================================")


def check_quality_gate(
    coverage_metrics: dict[str, Any], fail_under: int = DEFAULT_FAIL_UNDER
) -> bool:
    percent = coverage_metrics.get("percent_covered", 0)
    if percent is None:
        print("Coverage percent not found.")
        return False
    if percent < fail_under:
        print(f"FAIL: Coverage {percent}% is below threshold {fail_under}%")
        return False
    print(f"PASS: Coverage {percent}% meets threshold {fail_under}%")
    return True


def main():
    parser = argparse.ArgumentParser(description="UCKN Quality Metrics Dashboard")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary of test and coverage metrics",
    )
    parser.add_argument(
        "--check-gate",
        action="store_true",
        help="Check quality gate and exit nonzero if failed",
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=DEFAULT_FAIL_UNDER,
        help="Coverage threshold for quality gate",
    )
    args = parser.parse_args()

    pytest_json = load_pytest_json()
    pytest_metrics = summarize_pytest_results(pytest_json)
    coverage_json = load_coverage_json()
    if not coverage_json:
        print("No coverage.json found.")
        sys.exit(1)
    coverage_metrics = extract_coverage_metrics(coverage_json)

    if args.summary:
        print_summary(pytest_metrics, coverage_metrics)
        print("Coverage trend:")
        print_trend = True
        try:
            print_trend = True
            print()
            print_coverage_trend()
        except Exception:
            print_trend = False
        if not print_trend:
            print("No coverage trend available.")

    if args.check_gate:
        ok = check_quality_gate(coverage_metrics, args.fail_under)
        if not ok:
            sys.exit(2)
        else:
            print("Quality gate passed.")

    if not args.summary and not args.check_gate:
        print_summary(pytest_metrics, coverage_metrics)
        print("Tip: Use --summary or --check-gate for more options.")


if __name__ == "__main__":
    main()
