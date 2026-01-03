from src.uckn.core.atoms.semantic_search_engine_optimized import ResourceMonitor


def test_resource_monitor_records():
    monitor = ResourceMonitor()
    monitor.record({"cpu": 10, "mem": 100})
    monitor.record({"cpu": 20, "mem": 200})
    usage = monitor.get_usage()
    assert len(usage) == 2
    assert usage[0][1]["cpu"] == 10
    assert usage[1][1]["mem"] == 200
