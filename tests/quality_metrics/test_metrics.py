"""
Test metrics utilities for UCKN.

- Test execution time tracking
- Test result analysis
- JSON report parsing
"""

import json
import os
from typing import Any, Dict, List

PYTEST_JSON = os.environ.get("UCKN_PYTEST_JSON", "pytest-report.json")


def load_pytest_json(path: str = PYTEST_JSON) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def get_test_durations(pytest_json: dict[str, Any]) -> list[dict[str, Any]]:
    durations = []
    for test in pytest_json.get("tests", []):
        durations.append({
            "nodeid": test.get("nodeid"),
            "outcome": test.get("outcome"),
            "duration": test.get("duration", 0.0),
        })
    return durations


def slowest_tests(pytest_json: dict[str, Any], n: int = 10) -> list[dict[str, Any]]:
    durations = get_test_durations(pytest_json)
    return sorted(durations, key=lambda x: x["duration"], reverse=True)[:n]


def print_slowest_tests(pytest_json: dict[str, Any], n: int = 10):
    slow = slowest_tests(pytest_json, n)
    print(f"Top {n} slowest tests:")
    for t in slow:
        print(f"{t['nodeid']}: {t['duration']:.2f}s ({t['outcome']})")


def main():
    pytest_json = load_pytest_json()
    if not pytest_json:
        print("No pytest-report.json found.")
        return
    print_slowest_tests(pytest_json, 10)


if __name__ == "__main__":
    main()
