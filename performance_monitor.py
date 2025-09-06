"""
Performance monitoring and metrics collection
"""
import time
import psutil
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import json
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    open_files: int


@dataclass
class TaskMetrics:
    """Metrics for a specific task"""
    task_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_peak_mb: float = 0.0
    cpu_peak_percent: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    input_size_mb: float = 0.0
    output_size_mb: float = 0.0


class PerformanceMonitor:
    """Monitors system and application performance"""
    
    def __init__(self, log_interval: float = 5.0, log_file: Optional[str] = None):
        """
        Initialize performance monitor
        
        Args:
            log_interval: Interval in seconds between system metrics collection
            log_file: Optional file to log metrics to
        """
        self.log_interval = log_interval
        self.log_file = log_file
        self.metrics: List[PerformanceMetrics] = []
        self.task_metrics: List[TaskMetrics] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.start_time = time.time()
        
        # Get initial system state
        self.initial_disk_io = psutil.disk_io_counters()
        self.initial_network_io = psutil.net_io_counters()
        
    def start_monitoring(self):
        """Start background monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(self.log_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.log_interval)
    
    def _collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            # Get process info
            process = psutil.Process()
            
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Get disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = (disk_io.read_bytes - self.initial_disk_io.read_bytes) / (1024 * 1024)
            disk_write_mb = (disk_io.write_bytes - self.initial_disk_io.write_bytes) / (1024 * 1024)
            
            # Get network I/O
            network_io = psutil.net_io_counters()
            network_sent_mb = (network_io.bytes_sent - self.initial_network_io.bytes_sent) / (1024 * 1024)
            network_recv_mb = (network_io.bytes_recv - self.initial_network_io.bytes_recv) / (1024 * 1024)
            
            # Get process-specific info
            process_memory = process.memory_info()
            memory_mb = process_memory.rss / (1024 * 1024)
            memory_percent = process.memory_percent()
            
            # Get thread and file info
            active_threads = process.num_threads()
            try:
                open_files = len(process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0
            
            # Create metrics object
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_threads=active_threads,
                open_files=open_files
            )
            
            self.metrics.append(metrics)
            
            # Log to file if specified
            if self.log_file:
                self._log_metrics_to_file(metrics)
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _log_metrics_to_file(self, metrics: PerformanceMetrics):
        """Log metrics to file"""
        try:
            log_entry = {
                'timestamp': metrics.timestamp,
                'cpu_percent': metrics.cpu_percent,
                'memory_mb': metrics.memory_mb,
                'memory_percent': metrics.memory_percent,
                'disk_io_read_mb': metrics.disk_io_read_mb,
                'disk_io_write_mb': metrics.disk_io_write_mb,
                'network_sent_mb': metrics.network_sent_mb,
                'network_recv_mb': metrics.network_recv_mb,
                'active_threads': metrics.active_threads,
                'open_files': metrics.open_files
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging metrics to file: {e}")
    
    @contextmanager
    def monitor_task(self, task_name: str, input_size_mb: float = 0.0):
        """Context manager for monitoring individual tasks"""
        task_metrics = TaskMetrics(
            task_name=task_name,
            start_time=time.time(),
            input_size_mb=input_size_mb
        )
        
        try:
            yield task_metrics
            task_metrics.success = True
        except Exception as e:
            task_metrics.success = False
            task_metrics.error_message = str(e)
            raise
        finally:
            task_metrics.end_time = time.time()
            task_metrics.duration = task_metrics.end_time - task_metrics.start_time
            
            # Get peak resource usage during task
            if self.metrics:
                task_start_time = task_metrics.start_time
                task_end_time = task_metrics.end_time
                
                task_metrics_list = [
                    m for m in self.metrics 
                    if task_start_time <= m.timestamp <= task_end_time
                ]
                
                if task_metrics_list:
                    task_metrics.memory_peak_mb = max(m.memory_mb for m in task_metrics_list)
                    task_metrics.cpu_peak_percent = max(m.cpu_percent for m in task_metrics_list)
            
            self.task_metrics.append(task_metrics)
            logger.info(f"Task {task_name} completed in {task_metrics.duration:.2f}s")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics:
            return {"error": "No metrics collected"}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in self.metrics) / len(self.metrics)
        avg_memory_mb = sum(m.memory_mb for m in self.metrics) / len(self.metrics)
        avg_memory_percent = sum(m.memory_percent for m in self.metrics) / len(self.metrics)
        
        # Calculate peaks
        peak_cpu = max(m.cpu_percent for m in self.metrics)
        peak_memory_mb = max(m.memory_mb for m in self.metrics)
        peak_memory_percent = max(m.memory_percent for m in self.metrics)
        
        # Calculate totals
        total_disk_read = sum(m.disk_io_read_mb for m in self.metrics)
        total_disk_write = sum(m.disk_io_write_mb for m in self.metrics)
        total_network_sent = sum(m.network_sent_mb for m in self.metrics)
        total_network_recv = sum(m.network_recv_mb for m in self.metrics)
        
        # Task metrics
        successful_tasks = sum(1 for t in self.task_metrics if t.success)
        failed_tasks = sum(1 for t in self.task_metrics if not t.success)
        avg_task_duration = sum(t.duration for t in self.task_metrics if t.duration) / len(self.task_metrics) if self.task_metrics else 0
        
        return {
            'monitoring_duration': time.time() - self.start_time,
            'metrics_collected': len(self.metrics),
            'cpu': {
                'average_percent': avg_cpu,
                'peak_percent': peak_cpu
            },
            'memory': {
                'average_mb': avg_memory_mb,
                'peak_mb': peak_memory_mb,
                'average_percent': avg_memory_percent,
                'peak_percent': peak_memory_percent
            },
            'disk_io': {
                'total_read_mb': total_disk_read,
                'total_write_mb': total_disk_write
            },
            'network_io': {
                'total_sent_mb': total_network_sent,
                'total_recv_mb': total_network_recv
            },
            'tasks': {
                'total': len(self.task_metrics),
                'successful': successful_tasks,
                'failed': failed_tasks,
                'success_rate': successful_tasks / len(self.task_metrics) if self.task_metrics else 0,
                'average_duration': avg_task_duration
            }
        }
    
    def save_report(self, filepath: str):
        """Save detailed performance report to file"""
        report = {
            'summary': self.get_summary(),
            'system_metrics': [
                {
                    'timestamp': m.timestamp,
                    'cpu_percent': m.cpu_percent,
                    'memory_mb': m.memory_mb,
                    'memory_percent': m.memory_percent,
                    'disk_io_read_mb': m.disk_io_read_mb,
                    'disk_io_write_mb': m.disk_io_write_mb,
                    'network_sent_mb': m.network_sent_mb,
                    'network_recv_mb': m.network_recv_mb,
                    'active_threads': m.active_threads,
                    'open_files': m.open_files
                } for m in self.metrics
            ],
            'task_metrics': [
                {
                    'task_name': t.task_name,
                    'start_time': t.start_time,
                    'end_time': t.end_time,
                    'duration': t.duration,
                    'memory_peak_mb': t.memory_peak_mb,
                    'cpu_peak_percent': t.cpu_peak_percent,
                    'success': t.success,
                    'error_message': t.error_message,
                    'input_size_mb': t.input_size_mb,
                    'output_size_mb': t.output_size_mb
                } for t in self.task_metrics
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report saved to {filepath}")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()