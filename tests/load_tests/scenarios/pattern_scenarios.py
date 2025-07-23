"""
Locust scenario: Concurrent pattern addition for UCKN
"""

import random

from locust import HttpUser, TaskSet, tag, task

from ..utils.test_data_generator import generate_pattern


class PatternAdditionTaskSet(TaskSet):
    def on_start(self):
        self.pattern_count = 0

    @tag('add')
    @task(5)
    def add_pattern(self):
        pattern = generate_pattern()
        with self.client.post("/api/patterns/add", json=pattern, catch_response=True) as resp:
            if resp.status_code != 200 or "id" not in resp.json():
                resp.failure(f"Pattern addition failed: {resp.text}")
            else:
                self.pattern_count += 1

class PatternAdditionUser(HttpUser):
    tasks = [PatternAdditionTaskSet]
    # wait_time is set in locustfile.py
