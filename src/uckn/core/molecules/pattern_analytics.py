"""
UCKN Pattern Analytics Molecule

Tracks and analyzes pattern application attempts, outcomes, and quality metrics.
Provides real-time and batch analytics for knowledge pattern effectiveness.
"""

import logging
import statistics
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from ...storage.chromadb_connector import ChromaDBConnector


class PatternAnalytics:
    """
    Tracks pattern application attempts, calculates metrics, and provides analytics.
    """

    APPLICATION_COLLECTION = "pattern_applications"
    PATTERN_COLLECTION = "code_patterns"

    def __init__(self, chroma_connector: ChromaDBConnector):
        self.chroma_connector = chroma_connector
        self._logger = logging.getLogger(__name__)
        self._ensure_application_collection()

    def _ensure_application_collection(self):
        """
        Ensure the pattern_applications collection exists in ChromaDB.
        """
        if not hasattr(self.chroma_connector, "collections"):
            self._logger.error("ChromaDBConnector missing 'collections' attribute.")
            return
        if self.APPLICATION_COLLECTION not in self.chroma_connector.collections:
            try:
                self.chroma_connector.collections[self.APPLICATION_COLLECTION] = (
                    self.chroma_connector.client.get_or_create_collection(
                        name=self.APPLICATION_COLLECTION,
                        metadata={"description": "UCKN pattern application attempts"},
                    )
                )
                self._logger.info(
                    f"ChromaDB collection '{self.APPLICATION_COLLECTION}' initialized."
                )
            except Exception as e:
                self._logger.error(
                    f"Failed to create pattern_applications collection: {e}"
                )

    def record_application(
        self,
        pattern_id: str,
        context: dict[str, Any] | None = None,
        application_id: str | None = None,
        timestamp: str | None = None,
    ) -> str | None:
        """
        Record a pattern application attempt (pending outcome).

        Returns the application_id.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot record application.")
            return None

        application_id = application_id or str(uuid.uuid4())
        timestamp = timestamp or datetime.now().isoformat()
        record = {
            "application_id": application_id,
            "pattern_id": pattern_id,
            "timestamp": timestamp,
            "outcome": "pending",
            "resolution_time_minutes": None,
            "context": context or {},
            "failure_reason": None,
        }
        try:
            self.chroma_connector.add_document(
                collection_name=self.APPLICATION_COLLECTION,
                doc_id=application_id,
                document=f"Pattern application for {pattern_id}",
                embedding=[0.0],  # Placeholder, not used for analytics
                metadata=record,
            )
            self._logger.info(
                f"Recorded pattern application {application_id} for pattern {pattern_id}."
            )
            return application_id
        except Exception as e:
            self._logger.error(f"Failed to record application: {e}")
            return None

    def record_outcome(
        self,
        application_id: str,
        outcome: str,
        resolution_time_minutes: float | None = None,
        failure_reason: str | None = None,
    ) -> bool:
        """
        Record the outcome (success/failure) and timing for a pattern application.
        """
        if not self.chroma_connector.is_available():
            self._logger.warning("ChromaDB not available, cannot record outcome.")
            return False

        app_record = self.chroma_connector.get_document(
            self.APPLICATION_COLLECTION, application_id
        )
        if not app_record:
            self._logger.error(f"Application record {application_id} not found.")
            return False

        metadata = app_record["metadata"]
        metadata["outcome"] = outcome
        if resolution_time_minutes is not None:
            metadata["resolution_time_minutes"] = resolution_time_minutes
        if failure_reason:
            metadata["failure_reason"] = failure_reason

        success = self.chroma_connector.update_document(
            collection_name=self.APPLICATION_COLLECTION,
            doc_id=application_id,
            metadata=metadata,
        )
        if success:
            self._logger.info(
                f"Recorded outcome '{outcome}' for application {application_id}."
            )
            # Optionally, update pattern aggregate metrics
            self._update_pattern_metrics(metadata["pattern_id"])
        return success

    def get_pattern_metrics(self, pattern_id: str) -> dict[str, Any]:
        """
        Get all analytics metrics for a specific pattern.
        """
        applications = self._get_applications_for_pattern(pattern_id)
        if not applications:
            return {
                "pattern_id": pattern_id,
                "success_rate": None,
                "confidence_interval": None,
                "average_resolution_time": None,
                "application_count": 0,
                "quality_score": None,
                "trend": [],
            }
        success_rate, conf_int = self.calculate_success_rate(applications)
        avg_time = self._calculate_average_resolution_time(applications)
        quality_score = self.calculate_quality_score(applications)
        trend = self.get_trend_analysis(pattern_id)
        return {
            "pattern_id": pattern_id,
            "success_rate": success_rate,
            "confidence_interval": conf_int,
            "average_resolution_time": avg_time,
            "application_count": len(applications),
            "quality_score": quality_score,
            "trend": trend,
        }

    def calculate_success_rate(
        self, applications: list[dict[str, Any]] | None = None
    ) -> tuple[float | None, tuple[float, float] | None]:
        """
        Calculate success rate and 95% confidence interval using Wilson score interval.
        """
        if applications is None:
            self._logger.error(
                "Applications list required for success rate calculation."
            )
            return None, None
        n = len(applications)
        if n == 0:
            return None, None
        successes = sum(
            1 for app in applications if app["metadata"].get("outcome") == "success"
        )
        p = successes / n
        # Wilson score interval for binomial proportion
        z = 1.96  # 95% confidence
        denominator = 1 + z**2 / n
        centre = p + z**2 / (2 * n)
        margin = z * ((p * (1 - p) / n + z**2 / (4 * n**2)) ** 0.5)
        lower = (centre - margin) / denominator
        upper = (centre + margin) / denominator
        return p, (max(0.0, lower), min(1.0, upper))

    def _calculate_average_resolution_time(
        self, applications: list[dict[str, Any]]
    ) -> float | None:
        """
        Calculate weighted average resolution time for successful applications.
        """
        times = [
            app["metadata"].get("resolution_time_minutes")
            for app in applications
            if app["metadata"].get("outcome") == "success"
            and app["metadata"].get("resolution_time_minutes") is not None
        ]
        if not times:
            return None
        return float(statistics.mean(times))

    def calculate_quality_score(
        self, applications: list[dict[str, Any]]
    ) -> float | None:
        """
        Composite quality score: (success_rate * 0.4) + (time_score * 0.3) + (usage_score * 0.3)
        """
        n = len(applications)
        if n == 0:
            return None
        success_rate, _ = self.calculate_success_rate(applications)
        avg_time = self._calculate_average_resolution_time(applications)
        usage_score = min(1.0, n / 100)  # Normalize usage to [0,1] (100+ = 1.0)
        # Time score: inverse, best is 0 min, worst is 60+ min
        if avg_time is not None:
            time_score = max(0.0, min(1.0, 1.0 - (avg_time / 60.0)))
        else:
            time_score = 0.5  # Neutral if unknown
        if success_rate is None:
            return None
        quality = (success_rate * 0.4) + (time_score * 0.3) + (usage_score * 0.3)
        return round(quality, 4)

    def get_trend_analysis(
        self, pattern_id: str, days: int = 30, interval: str = "day"
    ) -> list[dict[str, Any]]:
        """
        Analyze trends in success rate and usage over time.
        Returns a list of dicts: [{"date": ..., "success_rate": ..., "count": ...}, ...]
        """
        applications = self._get_applications_for_pattern(pattern_id)
        if not applications:
            return []
        now = datetime.now()
        buckets = defaultdict(list)
        for app in applications:
            ts = app["metadata"].get("timestamp")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
            except Exception:
                continue
            if (now - dt).days > days:
                continue
            key = dt.date() if interval == "day" else dt.strftime("%Y-%m")
            buckets[key].append(app)
        trend = []
        for key in sorted(buckets):
            bucket_apps = buckets[key]
            rate, _ = self.calculate_success_rate(bucket_apps)
            trend.append(
                {"date": str(key), "success_rate": rate, "count": len(bucket_apps)}
            )
        return trend

    def get_top_performing_patterns(
        self, top_n: int = 5, min_applications: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get top patterns by quality score.
        """
        all_apps = self._get_all_applications()
        pattern_groups = defaultdict(list)
        for app in all_apps:
            pid = app["metadata"].get("pattern_id")
            if pid:
                pattern_groups[pid].append(app)
        scored = []
        for pid, apps in pattern_groups.items():
            if len(apps) < min_applications:
                continue
            score = self.calculate_quality_score(apps)
            if score is not None:
                scored.append((pid, score, len(apps)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {"pattern_id": pid, "quality_score": score, "application_count": count}
            for pid, score, count in scored[:top_n]
        ]

    def get_problematic_patterns(
        self, threshold: float = 0.5, min_applications: int = 5
    ) -> list[dict[str, Any]]:
        """
        Identify patterns with low success rates.
        """
        all_apps = self._get_all_applications()
        pattern_groups = defaultdict(list)
        for app in all_apps:
            pid = app["metadata"].get("pattern_id")
            if pid:
                pattern_groups[pid].append(app)
        problematic = []
        for pid, apps in pattern_groups.items():
            if len(apps) < min_applications:
                continue
            rate, _ = self.calculate_success_rate(apps)
            if rate is not None and rate < threshold:
                problematic.append(
                    {
                        "pattern_id": pid,
                        "success_rate": rate,
                        "application_count": len(apps),
                    }
                )
        problematic.sort(key=lambda x: x["success_rate"])
        return problematic

    def _get_applications_for_pattern(self, pattern_id: str) -> list[dict[str, Any]]:
        """
        Retrieve all application records for a given pattern.
        """
        if not self.chroma_connector.is_available():
            return []
        try:
            results = self.chroma_connector.search_documents(
                collection_name=self.APPLICATION_COLLECTION,
                query_embedding=[0.0],  # Not used, but required by API
                n_results=10000,
                min_similarity=0.0,
                where_clause={"pattern_id": pattern_id},
            )
            return results
        except Exception as e:
            self._logger.error(
                f"Failed to get applications for pattern {pattern_id}: {e}"
            )
            return []

    def _get_all_applications(self) -> list[dict[str, Any]]:
        """
        Retrieve all application records.
        """
        if not self.chroma_connector.is_available():
            return []
        try:
            return self.chroma_connector.get_all_documents(self.APPLICATION_COLLECTION)
        except Exception as e:
            self._logger.error(f"Failed to get all pattern applications: {e}")
            return []

    def _update_pattern_metrics(self, pattern_id: str):
        """
        Update aggregated metrics in the code_patterns collection metadata.
        """
        metrics = self.get_pattern_metrics(pattern_id)
        pattern = self.chroma_connector.get_document(
            self.PATTERN_COLLECTION, pattern_id
        )
        if not pattern:
            self._logger.warning(f"Pattern {pattern_id} not found for metrics update.")
            return
        metadata = pattern["metadata"]
        metadata["success_rate"] = metrics["success_rate"]
        metadata["confidence_interval"] = metrics["confidence_interval"]
        metadata["average_resolution_time"] = metrics["average_resolution_time"]
        metadata["application_count"] = metrics["application_count"]
        metadata["quality_score"] = metrics["quality_score"]
        try:
            self.chroma_connector.update_document(
                collection_name=self.PATTERN_COLLECTION,
                doc_id=pattern_id,
                metadata=metadata,
            )
            self._logger.info(f"Updated pattern {pattern_id} aggregated metrics.")
        except Exception as e:
            self._logger.error(
                f"Failed to update pattern metrics for {pattern_id}: {e}"
            )

    # Batch analysis for historical data
    def batch_update_all_pattern_metrics(self):
        """
        Recalculate and update metrics for all patterns.
        """
        if not self.chroma_connector.is_available():
            return
        try:
            patterns = self.chroma_connector.get_all_documents(self.PATTERN_COLLECTION)
            for pattern in patterns:
                pid = pattern["id"]
                self._update_pattern_metrics(pid)
            self._logger.info("Batch update of all pattern metrics complete.")
        except Exception as e:
            self._logger.error(f"Batch update failed: {e}")
