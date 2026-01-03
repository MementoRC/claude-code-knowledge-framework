from src.uckn.core.atoms.semantic_search_engine_optimized import PerformanceAnalytics


def test_analytics_log_and_summary():
    analytics = PerformanceAnalytics()
    analytics.log("event1", 123)
    analytics.log("event2", 456)
    summary = analytics.summary()
    assert "event1" in summary
    assert summary["event2"] == 456
