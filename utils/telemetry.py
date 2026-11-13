import sys
import time
from datetime import datetime
from collections import deque
from typing import Dict, Any

class TelemetryCollector:
    """Enterprise performance, observability, and health telemetry engine."""
    
    def __init__(self, max_history: int = 500):
        self.start_time = time.monotonic()
        self.started_at = datetime.now()
        self.total_updates = 0
        self.total_errors = 0
        self.latencies = deque(maxlen=max_history)
        self.command_counts: Dict[str, int] = {}

    def record_update(self, latency_ms: float, command: str = None):
        """Record processed update execution metric"""
        self.total_updates += 1
        self.latencies.append(latency_ms)
        if command:
            self.command_counts[command] = self.command_counts.get(command, 0) + 1

    def record_error(self):
        """Record an unhandled exception caught by boundary"""
        self.total_errors += 1

    def get_uptime_seconds(self) -> float:
        """Return runtime duration in seconds"""
        return time.monotonic() - self.start_time

    def get_uptime_formatted(self) -> str:
        """Return human-readable uptime string (e.g. 1d 4h 12m 30s)"""
        total_sec = int(self.get_uptime_seconds())
        days, rem = divmod(total_sec, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

    def get_latency_stats(self) -> Dict[str, float]:
        """Compute average and 95th percentile latency"""
        if not self.latencies:
            return {"avg_ms": 0.0, "p95_ms": 0.0}
        
        sorted_latencies = sorted(self.latencies)
        avg_ms = sum(sorted_latencies) / len(sorted_latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p95_ms = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]
        return {
            "avg_ms": round(avg_ms, 2),
            "p95_ms": round(p95_ms, 2)
        }

    def get_memory_usage_mb(self) -> float:
        """Estimate current process RSS memory in megabytes (cross-platform)"""
        try:
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes
                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [
                        ('cb', wintypes.DWORD),
                        ('PageFaultCount', wintypes.DWORD),
                        ('PeakWorkingSetSize', ctypes.c_size_t),
                        ('WorkingSetSize', ctypes.c_size_t),
                        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                        ('PagefileUsage', ctypes.c_size_t),
                        ('PeakPagefileUsage', ctypes.c_size_t),
                    ]
                counters = PROCESS_MEMORY_COUNTERS()
                counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
                if ctypes.windll.psapi.GetProcessMemoryInfo(
                    ctypes.windll.kernel32.GetCurrentProcess(),
                    ctypes.byref(counters),
                    counters.cb
                ):
                    return round(counters.WorkingSetSize / (1024 * 1024), 2)
            else:
                import resource
                # ru_maxrss is in kilobytes on Linux
                return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)
        except Exception:
            pass
        return 0.0

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Produce full health and metrics snapshot for health-check and admin dashboard"""
        lat_stats = self.get_latency_stats()
        return {
            "started_at": self.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": self.get_uptime_formatted(),
            "uptime_seconds": round(self.get_uptime_seconds(), 1),
            "total_updates": self.total_updates,
            "total_errors": self.total_errors,
            "avg_latency_ms": lat_stats["avg_ms"],
            "p95_latency_ms": lat_stats["p95_ms"],
            "memory_rss_mb": self.get_memory_usage_mb(),
            "python_version": sys.version.split()[0],
            "platform": sys.platform
        }

# Global singleton instance
telemetry = TelemetryCollector()
