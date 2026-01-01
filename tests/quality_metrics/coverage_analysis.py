"""
Coverage analysis utilities for UCKN quality metrics.

- Coverage trend analysis
- Differential coverage utilities
- Markdown/JSON summary generation
"""

import json
import os
from datetime import datetime
from typing import Any

COVERAGE_JSON = os.environ.get("UCKN_COVERAGE_JSON", "coverage.json")
COVERAGE_MD = os.environ.get("UCKN_COVERAGE_MD", "coverage.md")
COVERAGE_HISTORY = os.environ.get("UCKN_COVERAGE_HISTORY", "coverage_history.json")


def load_coverage_json(path: str = COVERAGE_JSON) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def extract_coverage_metrics(coverage: dict[str, Any]) -> dict[str, Any]:
    totals = coverage.get("totals", {})
    return {
        "covered_lines": totals.get("covered_lines"),
        "num_statements": totals.get("num_statements"),
        "percent_covered": totals.get("percent_covered"),
        "missing_lines": totals.get("missing_lines"),
        "percent_branches_covered": totals.get("percent_branches_covered"),
        "missing_branches": totals.get("missing_branches"),
        "timestamp": datetime.utcnow().isoformat(),
    }


def save_coverage_history(metrics: dict[str, Any], path: str = COVERAGE_HISTORY):
    history = []
    if os.path.exists(path):
        with open(path) as f:
            try:
                history = json.load(f)
            except Exception:
                history = []
    history.append(metrics)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def print_coverage_trend(path: str = COVERAGE_HISTORY):
    if not os.path.exists(path):
        print("No coverage history found.")
        return
    with open(path) as f:
        history = json.load(f)
    print("Coverage Trend:")
    for entry in history:
        print(
            f"{entry['timestamp']}: {entry['percent_covered']}% lines, {entry.get('percent_branches_covered', 'N/A')}% branches"
        )


def generate_markdown_summary(metrics: dict[str, Any], path: str = COVERAGE_MD):
    with open(path, "w") as f:
        f.write("# UCKN Coverage Summary\n\n")
        f.write(f"- **Line Coverage:** {metrics['percent_covered']}%\n")
        f.write(
            f"- **Branch Coverage:** {metrics.get('percent_branches_covered', 'N/A')}%\n"
        )
        f.write(f"- **Statements:** {metrics['num_statements']}\n")
        f.write(f"- **Covered Lines:** {metrics['covered_lines']}\n")
        f.write(f"- **Missing Lines:** {metrics['missing_lines']}\n")
        f.write(f"- **Missing Branches:** {metrics.get('missing_branches', 'N/A')}\n")
        f.write(f"- **Timestamp:** {metrics['timestamp']}\n")


def main():
    cov = load_coverage_json()
    if not cov:
        print("No coverage.json found.")
        return
    metrics = extract_coverage_metrics(cov)
    save_coverage_history(metrics)
    print_coverage_trend()
    generate_markdown_summary(metrics)
    print("Coverage analysis complete. Markdown summary and trend updated.")


if __name__ == "__main__":
    main()
