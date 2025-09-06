#!/usr/bin/env python3
"""
Performance monitoring and profiling for HackReporter
Provides real-time performance metrics and optimization recommendations
"""

import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    load_avg: Optional[float] = None

class PerformanceMonitor:
    """Real-time performance monitoring for HackReporter"""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.metrics: List[PerformanceMetrics] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.start_time = time.time()
        
        # Baseline measurements
        self.initial_disk_io = psutil.disk_io_counters()
        self.initial_network = psutil.net_io_counters()
        
    def start_monitoring(self):
        """Start performance monitoring in background thread"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔍 Performance monitoring started")
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("⏹️  Performance monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics.append(metrics)
                
                # Keep only last 100 measurements to avoid memory growth
                if len(self.metrics) > 100:
                    self.metrics = self.metrics[-100:]
                    
                time.sleep(self.monitoring_interval)
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics"""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        # Disk I/O
        current_disk_io = psutil.disk_io_counters()
        disk_read_mb = (current_disk_io.read_bytes - self.initial_disk_io.read_bytes) / (1024**2)
        disk_write_mb = (current_disk_io.write_bytes - self.initial_disk_io.write_bytes) / (1024**2)
        
        # Network I/O
        current_network = psutil.net_io_counters()
        network_sent_mb = (current_network.bytes_sent - self.initial_network.bytes_sent) / (1024**2)
        network_recv_mb = (current_network.bytes_recv - self.initial_network.bytes_recv) / (1024**2)
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Unix systems only)
        load_avg = None
        try:
            load_avg = psutil.getloadavg()[0]  # 1-minute load average
        except AttributeError:
            pass  # Windows doesn't have load average
            
        return PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_mb=memory.used / (1024**2),
            memory_percent=memory.percent,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            process_count=process_count,
            load_avg=load_avg
        )
        
    def get_current_stats(self) -> Dict:
        """Get current performance statistics"""
        if not self.metrics:
            return {"error": "No metrics collected yet"}
            
        latest = self.metrics[-1]
        runtime_minutes = (time.time() - self.start_time) / 60
        
        return {
            "runtime_minutes": round(runtime_minutes, 2),
            "current_cpu_percent": latest.cpu_percent,
            "current_memory_mb": round(latest.memory_mb, 1),
            "current_memory_percent": latest.memory_percent,
            "total_disk_read_mb": round(latest.disk_io_read_mb, 1),
            "total_disk_write_mb": round(latest.disk_io_write_mb, 1),
            "total_network_sent_mb": round(latest.network_sent_mb, 1),
            "total_network_recv_mb": round(latest.network_recv_mb, 1),
            "process_count": latest.process_count,
            "load_average": latest.load_avg
        }
        
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        if len(self.metrics) < 2:
            return {"error": "Insufficient metrics for summary"}
            
        # Calculate averages and peaks
        cpu_values = [m.cpu_percent for m in self.metrics]
        memory_values = [m.memory_percent for m in self.metrics]
        
        summary = {
            "monitoring_duration_minutes": round((time.time() - self.start_time) / 60, 2),
            "samples_collected": len(self.metrics),
            "cpu_usage": {
                "average": round(sum(cpu_values) / len(cpu_values), 1),
                "peak": round(max(cpu_values), 1),
                "minimum": round(min(cpu_values), 1)
            },
            "memory_usage": {
                "average_percent": round(sum(memory_values) / len(memory_values), 1),
                "peak_percent": round(max(memory_values), 1),
                "current_mb": round(self.metrics[-1].memory_mb, 1)
            },
            "disk_io": {
                "total_read_mb": round(self.metrics[-1].disk_io_read_mb, 1),
                "total_write_mb": round(self.metrics[-1].disk_io_write_mb, 1)
            },
            "network_io": {
                "total_sent_mb": round(self.metrics[-1].network_sent_mb, 1),
                "total_received_mb": round(self.metrics[-1].network_recv_mb, 1)
            }
        }
        
        # Add optimization recommendations
        summary["recommendations"] = self._generate_recommendations(summary)
        
        return summary
        
    def _generate_recommendations(self, summary: Dict) -> List[str]:
        """Generate optimization recommendations based on metrics"""
        recommendations = []
        
        # CPU recommendations
        if summary["cpu_usage"]["average"] > 80:
            recommendations.append("High CPU usage detected. Consider reducing concurrent video processing.")
        elif summary["cpu_usage"]["average"] < 30:
            recommendations.append("Low CPU usage. You could potentially increase concurrent processing.")
            
        # Memory recommendations
        if summary["memory_usage"]["average_percent"] > 85:
            recommendations.append("High memory usage. Enable memory optimization and reduce batch sizes.")
        elif summary["memory_usage"]["peak_percent"] > 95:
            recommendations.append("Memory usage peaked very high. Consider sequential processing mode.")
            
        # Disk I/O recommendations
        total_disk_io = summary["disk_io"]["total_read_mb"] + summary["disk_io"]["total_write_mb"]
        if total_disk_io > 1000:  # More than 1GB of disk I/O
            recommendations.append("High disk I/O detected. Consider enabling caching and optimizing file operations.")
            
        # Network recommendations
        total_network = summary["network_io"]["total_sent_mb"] + summary["network_io"]["total_received_mb"]
        if total_network > 500:  # More than 500MB network usage
            recommendations.append("High network usage. API calls are significant - consider caching results.")
            
        if not recommendations:
            recommendations.append("Performance looks good! Current settings appear optimal.")
            
        return recommendations
        
    def save_metrics(self, filepath: str = "performance_metrics.json"):
        """Save collected metrics to file"""
        metrics_data = {
            "start_time": self.start_time,
            "monitoring_interval": self.monitoring_interval,
            "metrics": [
                {
                    "timestamp": m.timestamp,
                    "cpu_percent": m.cpu_percent,
                    "memory_mb": m.memory_mb,
                    "memory_percent": m.memory_percent,
                    "disk_io_read_mb": m.disk_io_read_mb,
                    "disk_io_write_mb": m.disk_io_write_mb,
                    "network_sent_mb": m.network_sent_mb,
                    "network_recv_mb": m.network_recv_mb,
                    "process_count": m.process_count,
                    "load_avg": m.load_avg
                }
                for m in self.metrics
            ],
            "summary": self.get_performance_summary()
        }
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        print(f"📊 Performance metrics saved to {filepath}")

def main():
    """Demo of performance monitoring"""
    monitor = PerformanceMonitor(monitoring_interval=0.5)
    monitor.start_monitoring()
    
    try:
        # Simulate some work
        print("Simulating workload for 10 seconds...")
        time.sleep(10)
        
        # Show current stats
        stats = monitor.get_current_stats()
        print("\n📊 Current Performance Stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
        # Show summary
        summary = monitor.get_performance_summary()
        print("\n📈 Performance Summary:")
        print(f"   Duration: {summary['monitoring_duration_minutes']} minutes")
        print(f"   Avg CPU: {summary['cpu_usage']['average']}%")
        print(f"   Peak Memory: {summary['memory_usage']['peak_percent']}%")
        
        print("\n💡 Recommendations:")
        for rec in summary["recommendations"]:
            print(f"   - {rec}")
            
    finally:
        monitor.stop_monitoring()
        monitor.save_metrics()

if __name__ == "__main__":
    main()