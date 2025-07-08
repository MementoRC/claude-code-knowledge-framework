"""
Test Pattern Analytics functionality
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from uckn.core.molecules.pattern_analytics import PatternAnalytics


class TestPatternAnalytics:
    """Test PatternAnalytics functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_chroma = Mock()
        self.mock_chroma.is_available.return_value = True
        self.mock_chroma.client = Mock()
        self.mock_chroma.collections = {}
        self.analytics = PatternAnalytics(self.mock_chroma)

    def test_initialization(self):
        """Test PatternAnalytics initializes correctly"""
        assert self.analytics.chroma_connector == self.mock_chroma
        assert self.analytics.APPLICATION_COLLECTION == "pattern_applications"
        assert self.analytics.PATTERN_COLLECTION == "code_patterns"

    def test_record_application_success(self):
        """Test recording a pattern application attempt"""
        self.mock_chroma.add_document.return_value = True

        app_id = self.analytics.record_application(
            pattern_id="pattern-123",
            context={"technology_stack": ["python"], "project_type": "ml"},
        )

        assert app_id is not None
        self.mock_chroma.add_document.assert_called_once()
        call_args = self.mock_chroma.add_document.call_args
        assert call_args[1]["collection_name"] == "pattern_applications"
        assert call_args[1]["metadata"]["pattern_id"] == "pattern-123"
        assert call_args[1]["metadata"]["outcome"] == "pending"

    def test_record_application_unavailable(self):
        """Test recording when ChromaDB is unavailable"""
        self.mock_chroma.is_available.return_value = False

        app_id = self.analytics.record_application("pattern-123")

        assert app_id is None
        self.mock_chroma.add_document.assert_not_called()

    def test_calculate_success_rate_basic(self):
        """Test basic success rate calculation"""
        applications = [
            {"metadata": {"outcome": "success"}},
            {"metadata": {"outcome": "success"}},
            {"metadata": {"outcome": "failure"}},
            {"metadata": {"outcome": "success"}},
        ]

        success_rate, conf_interval = self.analytics.calculate_success_rate(
            applications
        )

        assert success_rate == 0.75  # 3/4
        assert conf_interval is not None
        assert 0.0 <= conf_interval[0] <= conf_interval[1] <= 1.0

    def test_calculate_success_rate_empty(self):
        """Test success rate calculation with empty applications"""
        success_rate, conf_interval = self.analytics.calculate_success_rate([])

        assert success_rate is None
        assert conf_interval is None

    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        applications = [
            {"metadata": {"outcome": "success", "resolution_time_minutes": 10.0}},
            {"metadata": {"outcome": "success", "resolution_time_minutes": 20.0}},
            {"metadata": {"outcome": "failure", "resolution_time_minutes": 30.0}},
        ]

        quality_score = self.analytics.calculate_quality_score(applications)

        assert quality_score is not None
        assert 0.0 <= quality_score <= 1.0
        # Should be > 0 since we have some successes and reasonable times
        assert quality_score > 0.0

    def test_get_pattern_metrics_no_applications(self):
        """Test getting metrics when no applications exist"""
        with patch.object(
            self.analytics, "_get_applications_for_pattern"
        ) as mock_get_apps:
            mock_get_apps.return_value = []

            metrics = self.analytics.get_pattern_metrics("pattern-123")

        assert metrics["pattern_id"] == "pattern-123"
        assert metrics["success_rate"] is None
        assert metrics["confidence_interval"] is None
        assert metrics["average_resolution_time"] is None
        assert metrics["application_count"] == 0
        assert metrics["quality_score"] is None
        assert metrics["trend"] == []
