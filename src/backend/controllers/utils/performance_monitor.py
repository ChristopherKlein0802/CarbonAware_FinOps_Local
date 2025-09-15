#!/usr/bin/env python3
"""
Performance Monitoring System
Carbon-Aware FinOps Dashboard - Bachelor Thesis

Provides comprehensive performance monitoring for dashboard operations:
- API response time tracking
- Dashboard rendering performance
- Memory usage monitoring
- Cache efficiency metrics
"""

import time
import logging
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import wraps
from collections import defaultdict, deque
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Thread-safe performance metrics collector."""
    
    def __init__(self, max_samples=1000):
        """Initialize performance metrics collector."""
        self.max_samples = max_samples
        self._lock = threading.Lock()
        
        # Metrics storage
        self.api_response_times = defaultdict(lambda: deque(maxlen=max_samples))
        self.dashboard_render_times = deque(maxlen=max_samples)
        self.memory_usage = deque(maxlen=max_samples)
        self.cache_hit_rates = defaultdict(lambda: {'hits': 0, 'misses': 0})
        
        # System info
        self.start_time = datetime.now()
        self.process = psutil.Process(os.getpid())
        
        logger.info("📊 Performance monitoring initialized")

    def record_api_response_time(self, api_name: str, response_time_ms: float):
        """Record API response time."""
        with self._lock:
            self.api_response_times[api_name].append({
                'timestamp': datetime.now(),
                'response_time_ms': response_time_ms
            })

    def record_dashboard_render_time(self, render_time_ms: float):
        """Record dashboard rendering time."""
        with self._lock:
            self.dashboard_render_times.append({
                'timestamp': datetime.now(),
                'render_time_ms': render_time_ms
            })

    def record_memory_usage(self):
        """Record current memory usage."""
        try:
            memory_info = self.process.memory_info()
            with self._lock:
                self.memory_usage.append({
                    'timestamp': datetime.now(),
                    'rss_mb': memory_info.rss / 1024 / 1024,  # Convert to MB
                    'vms_mb': memory_info.vms / 1024 / 1024
                })
        except Exception as e:
            logger.warning(f"Failed to record memory usage: {e}")

    def record_cache_hit(self, cache_name: str):
        """Record cache hit."""
        with self._lock:
            self.cache_hit_rates[cache_name]['hits'] += 1

    def record_cache_miss(self, cache_name: str):
        """Record cache miss."""
        with self._lock:
            self.cache_hit_rates[cache_name]['misses'] += 1

    def get_api_performance_summary(self) -> Dict:
        """Get API performance summary."""
        with self._lock:
            summary = {}
            
            for api_name, responses in self.api_response_times.items():
                if responses:
                    times = [r['response_time_ms'] for r in responses]
                    summary[api_name] = {
                        'avg_response_time_ms': sum(times) / len(times),
                        'min_response_time_ms': min(times),
                        'max_response_time_ms': max(times),
                        'total_requests': len(times),
                        'last_request': responses[-1]['timestamp'].isoformat()
                    }
            
            return summary

    def get_dashboard_performance_summary(self) -> Dict:
        """Get dashboard performance summary."""
        with self._lock:
            if not self.dashboard_render_times:
                return {'status': 'no_data'}
            
            render_times = [r['render_time_ms'] for r in self.dashboard_render_times]
            
            return {
                'avg_render_time_ms': sum(render_times) / len(render_times),
                'min_render_time_ms': min(render_times),
                'max_render_time_ms': max(render_times),
                'total_renders': len(render_times),
                'performance_grade': self._calculate_performance_grade(sum(render_times) / len(render_times))
            }

    def get_memory_usage_summary(self) -> Dict:
        """Get memory usage summary."""
        with self._lock:
            if not self.memory_usage:
                return {'status': 'no_data'}
            
            current_memory = self.memory_usage[-1]
            peak_rss = max(m['rss_mb'] for m in self.memory_usage)
            
            return {
                'current_rss_mb': current_memory['rss_mb'],
                'current_vms_mb': current_memory['vms_mb'],
                'peak_rss_mb': peak_rss,
                'memory_trend': self._calculate_memory_trend(),
                'memory_efficiency_grade': self._calculate_memory_grade(current_memory['rss_mb'])
            }

    def get_cache_efficiency_summary(self) -> Dict:
        """Get cache efficiency summary."""
        with self._lock:
            cache_summary = {}
            
            for cache_name, stats in self.cache_hit_rates.items():
                total = stats['hits'] + stats['misses']
                if total > 0:
                    hit_rate = (stats['hits'] / total) * 100
                    cache_summary[cache_name] = {
                        'hit_rate_percent': hit_rate,
                        'total_requests': total,
                        'hits': stats['hits'],
                        'misses': stats['misses'],
                        'efficiency_grade': self._calculate_cache_grade(hit_rate)
                    }
            
            return cache_summary

    def _calculate_performance_grade(self, avg_render_time_ms: float) -> str:
        """Calculate performance grade based on render time."""
        if avg_render_time_ms < 100:
            return 'A'
        elif avg_render_time_ms < 250:
            return 'B'
        elif avg_render_time_ms < 500:
            return 'C'
        elif avg_render_time_ms < 1000:
            return 'D'
        else:
            return 'F'

    def _calculate_memory_grade(self, current_rss_mb: float) -> str:
        """Calculate memory efficiency grade."""
        if current_rss_mb < 100:
            return 'A'
        elif current_rss_mb < 250:
            return 'B'
        elif current_rss_mb < 500:
            return 'C'
        elif current_rss_mb < 1000:
            return 'D'
        else:
            return 'F'

    def _calculate_cache_grade(self, hit_rate_percent: float) -> str:
        """Calculate cache efficiency grade."""
        if hit_rate_percent >= 90:
            return 'A'
        elif hit_rate_percent >= 80:
            return 'B'
        elif hit_rate_percent >= 70:
            return 'C'
        elif hit_rate_percent >= 60:
            return 'D'
        else:
            return 'F'

    def _calculate_memory_trend(self) -> str:
        """Calculate memory usage trend."""
        if len(self.memory_usage) < 10:
            return 'insufficient_data'
        
        recent = list(self.memory_usage)[-10:]
        older = list(self.memory_usage)[-20:-10] if len(self.memory_usage) >= 20 else recent[:5]
        
        recent_avg = sum(m['rss_mb'] for m in recent) / len(recent)
        older_avg = sum(m['rss_mb'] for m in older) / len(older)
        
        diff_percent = ((recent_avg - older_avg) / older_avg) * 100
        
        if diff_percent > 10:
            return 'increasing'
        elif diff_percent < -10:
            return 'decreasing'
        else:
            return 'stable'

    def get_system_overview(self) -> Dict:
        """Get comprehensive system performance overview."""
        uptime = datetime.now() - self.start_time
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'uptime_human': str(uptime).split('.')[0],  # Remove microseconds
            'api_performance': self.get_api_performance_summary(),
            'dashboard_performance': self.get_dashboard_performance_summary(),
            'memory_usage': self.get_memory_usage_summary(),
            'cache_efficiency': self.get_cache_efficiency_summary(),
            'overall_health_score': self._calculate_overall_health_score()
        }

    def _calculate_overall_health_score(self) -> int:
        """Calculate overall system health score (0-100)."""
        scores = []
        
        # Dashboard performance score
        dash_perf = self.get_dashboard_performance_summary()
        if dash_perf.get('performance_grade'):
            grade_scores = {'A': 100, 'B': 80, 'C': 60, 'D': 40, 'F': 20}
            scores.append(grade_scores.get(dash_perf['performance_grade'], 50))
        
        # Memory efficiency score
        mem_usage = self.get_memory_usage_summary()
        if mem_usage.get('memory_efficiency_grade'):
            grade_scores = {'A': 100, 'B': 80, 'C': 60, 'D': 40, 'F': 20}
            scores.append(grade_scores.get(mem_usage['memory_efficiency_grade'], 50))
        
        # Cache efficiency score (average of all caches)
        cache_summary = self.get_cache_efficiency_summary()
        if cache_summary:
            cache_scores = [
                {'A': 100, 'B': 80, 'C': 60, 'D': 40, 'F': 20}.get(cache['efficiency_grade'], 50)
                for cache in cache_summary.values()
            ]
            scores.append(sum(cache_scores) / len(cache_scores))
        
        return int(sum(scores) / len(scores)) if scores else 75  # Default to 75 if no data


# Global performance monitor instance
performance_monitor = PerformanceMetrics()


def monitor_api_performance(api_name: str):
    """Decorator to monitor API performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                response_time_ms = (time.time() - start_time) * 1000
                performance_monitor.record_api_response_time(api_name, response_time_ms)
                logger.debug(f"API {api_name} responded in {response_time_ms:.1f}ms")
                return result
            except Exception as e:
                response_time_ms = (time.time() - start_time) * 1000
                performance_monitor.record_api_response_time(api_name, response_time_ms)
                logger.warning(f"API {api_name} failed after {response_time_ms:.1f}ms: {e}")
                raise
        return wrapper
    return decorator


@contextmanager
def monitor_dashboard_render(component_name: str = "dashboard"):
    """Context manager to monitor dashboard rendering performance."""
    start_time = time.time()
    try:
        yield
    finally:
        render_time_ms = (time.time() - start_time) * 1000
        performance_monitor.record_dashboard_render_time(render_time_ms)
        logger.debug(f"Dashboard {component_name} rendered in {render_time_ms:.1f}ms")


class CacheMonitor:
    """Cache performance monitor."""
    
    def __init__(self, cache_name: str):
        self.cache_name = cache_name
    
    def record_hit(self):
        """Record cache hit."""
        performance_monitor.record_cache_hit(self.cache_name)
    
    def record_miss(self):
        """Record cache miss."""
        performance_monitor.record_cache_miss(self.cache_name)


# Memory monitoring thread
class MemoryMonitor(threading.Thread):
    """Background thread for continuous memory monitoring."""
    
    def __init__(self, interval_seconds: int = 30):
        super().__init__(daemon=True)
        self.interval_seconds = interval_seconds
        self.running = True
    
    def run(self):
        """Run memory monitoring loop."""
        while self.running:
            performance_monitor.record_memory_usage()
            time.sleep(self.interval_seconds)
    
    def stop(self):
        """Stop memory monitoring."""
        self.running = False


# Start memory monitoring when module is imported
_memory_monitor = MemoryMonitor()
_memory_monitor.start()

logger.info("🚀 Performance monitoring system initialized and running")


if __name__ == "__main__":
    # Performance monitoring CLI
    print("📊 Dashboard Performance Monitor")
    print("=" * 50)
    
    # Record some test data
    performance_monitor.record_api_response_time("test_api", 150.5)
    performance_monitor.record_dashboard_render_time(89.2)
    performance_monitor.record_memory_usage()
    
    # Show overview
    overview = performance_monitor.get_system_overview()
    print(f"Uptime: {overview['uptime_human']}")
    print(f"Overall Health Score: {overview['overall_health_score']}/100")
    
    api_perf = overview['api_performance']
    if api_perf:
        print("\nAPI Performance:")
        for api_name, stats in api_perf.items():
            print(f"  {api_name}: {stats['avg_response_time_ms']:.1f}ms avg")
    
    dash_perf = overview['dashboard_performance']
    if dash_perf.get('avg_render_time_ms'):
        print(f"\nDashboard Rendering: {dash_perf['avg_render_time_ms']:.1f}ms avg (Grade: {dash_perf['performance_grade']})")
    
    mem_usage = overview['memory_usage']
    if mem_usage.get('current_rss_mb'):
        print(f"Memory Usage: {mem_usage['current_rss_mb']:.1f}MB (Grade: {mem_usage['memory_efficiency_grade']})")