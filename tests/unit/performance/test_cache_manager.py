import pytest

from src.uckn.core.atoms.semantic_search_engine_optimized import CacheManager


def test_cache_set_and_get():
    cache = CacheManager(max_size=2)
    cache.set("a", 1)
    assert cache.get("a") == 1
    cache.set("b", 2)
    assert cache.get("b") == 2
    cache.set("c", 3)
    # "a" should be evicted (FIFO)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3

def test_cache_clear():
    cache = CacheManager()
    cache.set("x", 42)
    cache.clear()
    assert cache.get("x") is None
