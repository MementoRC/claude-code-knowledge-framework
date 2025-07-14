"""
Configuration for UCKN load tests.
"""

# Default load test parameters (can be overridden via env vars or CLI)
DEFAULTS = {
    "search_users": 200,
    "add_users": 50,
    "mixed_users": 100,
    "spawn_rate": 20,
    "large_dataset_size": 100000,
    "resource_stress_users": 500,
    "host": "http://localhost:8000",
    "run_time": "10m",
}
