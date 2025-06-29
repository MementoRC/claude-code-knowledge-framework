# UCKN Load Testing Infrastructure

This directory contains comprehensive load testing infrastructure for the UCKN framework, using [Locust](https://locust.io/) to simulate high-traffic and large data conditions.

## Features

- **Locust-based user simulation**: Realistic user behaviors for search, pattern addition, and mixed workloads.
- **Configurable scenarios**: Easily adjust user counts, spawn rates, and scenario types.
- **Large dataset scaling**: Supports testing with 1K to 1M+ patterns.
- **Performance monitoring**: Collects response times, throughput, error rates, and system resource usage.
- **CI/CD integration**: Ready for automated load testing in pipelines.
- **Docker Compose support**: Consistent, reproducible test environments.

## Directory Structure

- `locustfile.py` — Entry point for Locust, scenario selection, and user classes.
- `scenarios/` — Scenario definitions (search, add, mixed, scaling, stress).
- `utils/` — Utilities for data generation and monitoring.
- `config/` — Load test configuration files.

## Running Load Tests

### Prerequisites

- Install dependencies:  
  `pip install .[loadtest]`
- Ensure the UCKN server is running and accessible.

### Basic Usage

```sh
cd tests/load_tests
locust -f locustfile.py --host=http://localhost:8000
```

### Scenario Selection

You can select scenarios via the Locust web UI or by specifying user classes with the `--users` and `--spawn-rate` flags.

### Docker Compose

A sample `docker-compose.load-test.yml` is provided for running UCKN and Locust together.

```sh
docker compose -f docker-compose.load-test.yml up --build
```

## Customization

- Adjust user behavior and data generation in `scenarios/` and `utils/`.
- Tune load parameters in `config/load_test_config.py`.

## Metrics and Monitoring

- Locust provides real-time metrics in its web UI.
- Additional resource monitoring is available via `utils/monitoring.py`.

## CI/CD Integration

- Integrate load tests in your pipeline using the provided commands and Docker Compose setup.
