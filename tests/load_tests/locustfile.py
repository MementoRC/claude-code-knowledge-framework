"""
UCKN Load Testing Entry Point (Locust)
"""

import os

from locust import HttpUser, between, events

from .scenarios.mixed_workload import MixedWorkloadUser
from .scenarios.pattern_scenarios import PatternAdditionUser
from .scenarios.search_scenarios import SearchUser
from .utils.monitoring import start_resource_monitor, stop_resource_monitor


# Start resource monitoring at test start
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    start_resource_monitor()


# Stop resource monitoring at test stop
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stop_resource_monitor()


# User classes for Locust
class UCKNSearchUser(SearchUser):
    wait_time = between(0.1, 0.5)


class UCKNPatternAdditionUser(PatternAdditionUser):
    wait_time = between(0.2, 1.0)


class UCKNMixedWorkloadUser(MixedWorkloadUser):
    wait_time = between(0.1, 0.7)


# Locust will discover these user classes for scenario selection
