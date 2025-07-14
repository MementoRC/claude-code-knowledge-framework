# UCKN Quality Metrics & Coverage

This directory contains scripts and utilities for collecting, analyzing, and reporting test coverage and quality metrics for the UCKN framework.

## Features

- **Enhanced Coverage Reporting**: Generates HTML, XML, JSON, and Markdown coverage reports.
- **Branch Coverage**: Tracks branch and line coverage.
- **Differential Coverage**: Uses `diff-cover` to report coverage for pull requests.
- **Test Metrics**: Collects test execution times, pass/fail rates, and trends.
- **Quality Dashboard**: Provides scripts for trend analysis and quality gate enforcement.
- **CI/CD Integration**: Artifacts and PR comments for coverage and quality metrics.

## Usage

### Local

```bash
pytest --cov=src/uckn --cov-report=html --cov-report=xml --cov-report=json --cov-report=term --cov-report=markdown
python tests/quality_metrics/quality_dashboard.py --summary
```

### In CI

See `.github/workflows/quality-metrics.yml` for full integration.

## Scripts

- `quality_dashboard.py`: Main dashboard and quality gate script.
- `coverage_analysis.py`: Coverage trend and diff analysis utilities.
- `test_metrics.py`: Test execution and result metrics.

## Requirements

- `pytest`, `pytest-cov`, `pytest-json-report`, `pytest-html`, `diff-cover`, `coverage`, `pytest-xdist`, etc.

## Quality Gate

The default quality gate is set to **90%** coverage. This can be configured in `pyproject.toml` or via CLI.
