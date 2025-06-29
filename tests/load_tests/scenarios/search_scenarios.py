"""
Locust scenario: High-volume search simulation for UCKN
"""

from locust import TaskSet, task, tag, HttpUser
from ..utils.test_data_generator import generate_search_queries
import random

class SearchTaskSet(TaskSet):
    def on_start(self):
        self.queries = generate_search_queries()
        self.query_idx = 0

    @tag('search')
    @task(10)
    def search_patterns(self):
        # Cycle through generated queries
        query = self.queries[self.query_idx % len(self.queries)]
        self.query_idx += 1
        with self.client.post("/api/patterns/search", json={"query": query}, catch_response=True) as resp:
            if resp.status_code != 200 or "results" not in resp.json():
                resp.failure(f"Search failed: {resp.text}")

class SearchUser(HttpUser):
    tasks = [SearchTaskSet]
    # wait_time is set in locustfile.py
