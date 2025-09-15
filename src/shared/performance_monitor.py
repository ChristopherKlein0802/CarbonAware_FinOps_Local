"""
Performance Monitor - Shared Cross-Cutting Concern
Monitors API performance and caching across all services

Architecture:
- Shared utility for performance tracking
- Cross-cutting concern for all API services
- Production-ready monitoring patterns
- Cache hit rate tracking
"""

import time
import logging
from datetime import datetime
from typing import Dict, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class CacheMonitor:
    """Monitor cache performance and hit rates"""

    def __init__(self, cache_name: str):
        self.cache_name = cache_name
        self.hits = 0
        self.misses = 0
        self.last_reset = datetime.now()

    def record_hit(self):
        """Record a cache hit"""
        self.hits += 1

    def record_miss(self):
        """Record a cache miss"""
        self.misses += 1

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def get_stats(self) -> Dict[str, Any]:
        """Get complete cache statistics"""
        return {
            "cache_name": self.cache_name,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(self.get_hit_rate(), 2),
            "total_requests": self.hits + self.misses,
            "last_reset": self.last_reset.isoformat()
        }

    def reset_stats(self):
        """Reset cache statistics"""
        self.hits = 0
        self.misses = 0
        self.last_reset = datetime.now()


class PerformanceTracker:
    """Track API performance metrics"""

    def __init__(self):
        self.metrics = {}

    def record_api_call(self, api_name: str, response_time_ms: float, success: bool):
        """Record API call performance"""
        if api_name not in self.metrics:
            self.metrics[api_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "total_response_time_ms": 0,
                "last_call": None,
                "fastest_response_ms": float('inf'),
                "slowest_response_ms": 0
            }

        metric = self.metrics[api_name]
        metric["total_calls"] += 1
        metric["total_response_time_ms"] += response_time_ms
        metric["last_call"] = datetime.now().isoformat()

        if success:
            metric["successful_calls"] += 1

        # Track fastest/slowest
        if response_time_ms < metric["fastest_response_ms"]:
            metric["fastest_response_ms"] = response_time_ms
        if response_time_ms > metric["slowest_response_ms"]:
            metric["slowest_response_ms"] = response_time_ms

    def get_api_stats(self, api_name: str) -> Dict[str, Any]:
        """Get performance statistics for specific API"""
        if api_name not in self.metrics:
            return {"error": f"No metrics available for {api_name}"}

        metric = self.metrics[api_name]
        avg_response_time = (
            metric["total_response_time_ms"] / metric["total_calls"]
            if metric["total_calls"] > 0 else 0
        )

        success_rate = (
            (metric["successful_calls"] / metric["total_calls"]) * 100
            if metric["total_calls"] > 0 else 0
        )

        return {
            "api_name": api_name,
            "total_calls": metric["total_calls"],
            "successful_calls": metric["successful_calls"],
            "success_rate_percent": round(success_rate, 2),
            "average_response_time_ms": round(avg_response_time, 2),
            "fastest_response_ms": metric["fastest_response_ms"] if metric["fastest_response_ms"] != float('inf') else 0,
            "slowest_response_ms": metric["slowest_response_ms"],
            "last_call": metric["last_call"]
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for all APIs"""
        return {api_name: self.get_api_stats(api_name) for api_name in self.metrics.keys()}


# Global instances
performance_tracker = PerformanceTracker()


def monitor_api_performance(api_name: str):
    """
    Decorator to monitor API performance

    Usage:
        @monitor_api_performance("my_api")
        def my_api_call():
            # API call logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False

            try:
                result = func(*args, **kwargs)
                success = result is not None  # Consider non-None results as successful
                return result
            except Exception as e:
                logger.error(f"API call failed for {api_name}: {e}")
                raise
            finally:
                response_time_ms = (time.time() - start_time) * 1000
                performance_tracker.record_api_call(api_name, response_time_ms, success)

                if success:
                    logger.debug(f"✅ {api_name}: {response_time_ms:.1f}ms")
                else:
                    logger.warning(f"⚠️ {api_name}: {response_time_ms:.1f}ms (failed)")

        return wrapper
    return decorator