"""
Locust scenario: Mixed workload (80% search, 20% add) for UCKN
"""

from locust import HttpUser, TaskSet, tag, task

from ..utils.test_data_generator import generate_pattern, generate_search_queries


class MixedWorkloadTaskSet(TaskSet):
    def on_start(self):
        self.queries = generate_search_queries()
        self.query_idx = 0

    @tag("search")
    @task(8)
    def search_patterns(self):
        query = self.queries[self.query_idx % len(self.queries)]
        self.query_idx += 1
        with self.client.post(
            "/api/patterns/search", json={"query": query}, catch_response=True
        ) as resp:
            if resp.status_code != 200 or "results" not in resp.json():
                resp.failure(f"Search failed: {resp.text}")

    @tag("add")
    @task(2)
    def add_pattern(self):
        pattern = generate_pattern()
        with self.client.post(
            "/api/patterns/add", json=pattern, catch_response=True
        ) as resp:
            if resp.status_code != 200 or "id" not in resp.json():
                resp.failure(f"Pattern addition failed: {resp.text}")


class MixedWorkloadUser(HttpUser):
    tasks = [MixedWorkloadTaskSet]
    # wait_time is set in locustfile.py
