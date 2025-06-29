"""
UCKN Performance Configuration

- Centralized config for performance tuning
- Supports env vars and config files
"""

import os

class PerformanceConfig:
    """
    Loads and manages performance-related configuration.
    """
    def __init__(self):
        self.cache_max_size = int(os.getenv("UCKN_CACHE_MAX_SIZE", "2048"))
        self.cache_ttl = int(os.getenv("UCKN_CACHE_TTL", "900"))
        self.redis_host = os.getenv("UCKN_REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("UCKN_REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("UCKN_REDIS_DB", "0"))
        self.batch_size = int(os.getenv("UCKN_BATCH_SIZE", "128"))
        self.resource_monitor_interval = float(os.getenv("UCKN_RESOURCE_MONITOR_INTERVAL", "2.0"))
        self.cpu_threshold = float(os.getenv("UCKN_CPU_THRESHOLD", "90.0"))
        self.mem_threshold = float(os.getenv("UCKN_MEM_THRESHOLD", "90.0"))

    def as_dict(self):
        return {
            "cache_max_size": self.cache_max_size,
            "cache_ttl": self.cache_ttl,
            "redis_host": self.redis_host,
            "redis_port": self.redis_port,
            "redis_db": self.redis_db,
            "batch_size": self.batch_size,
            "resource_monitor_interval": self.resource_monitor_interval,
            "cpu_threshold": self.cpu_threshold,
            "mem_threshold": self.mem_threshold,
        }

performance_config = PerformanceConfig()