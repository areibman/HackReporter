"""
Memory optimization utilities for video processing
"""
import gc
import os
import psutil
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import shutil

logger = logging.getLogger(__name__)


class MemoryOptimizer:
    """Manages memory usage and optimization for video processing"""
    
    def __init__(self, max_memory_mb: int = 2048, cleanup_threshold: float = 0.8):
        """
        Initialize memory optimizer
        
        Args:
            max_memory_mb: Maximum memory usage in MB before cleanup
            cleanup_threshold: Memory usage threshold (0.0-1.0) to trigger cleanup
        """
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = cleanup_threshold
        self.temp_files: List[Path] = []
        self.process = psutil.Process()
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        memory_info = self.process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory_mb': memory_info.rss / (1024 * 1024),
            'process_memory_percent': self.process.memory_percent(),
            'system_memory_percent': system_memory.percent,
            'available_memory_mb': system_memory.available / (1024 * 1024),
            'total_memory_mb': system_memory.total / (1024 * 1024)
        }
    
    def should_cleanup(self) -> bool:
        """Check if memory cleanup is needed"""
        memory_stats = self.get_memory_usage()
        
        # Check if process memory exceeds threshold
        if memory_stats['process_memory_mb'] > self.max_memory_mb:
            return True
            
        # Check if system memory is low
        if memory_stats['system_memory_percent'] > (self.cleanup_threshold * 100):
            return True
            
        return False
    
    def cleanup_memory(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform memory cleanup operations
        
        Args:
            force: Force cleanup even if thresholds aren't met
            
        Returns:
            Dictionary with cleanup results
        """
        if not force and not self.should_cleanup():
            return {"cleaned": False, "reason": "No cleanup needed"}
        
        initial_memory = self.get_memory_usage()
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clean up temporary files
        temp_cleaned = self._cleanup_temp_files()
        
        # Get final memory usage
        final_memory = self.get_memory_usage()
        
        memory_freed = initial_memory['process_memory_mb'] - final_memory['process_memory_mb']
        
        logger.info(f"Memory cleanup: freed {memory_freed:.1f}MB, collected {collected} objects")
        
        return {
            "cleaned": True,
            "memory_freed_mb": memory_freed,
            "objects_collected": collected,
            "temp_files_cleaned": temp_cleaned,
            "initial_memory_mb": initial_memory['process_memory_mb'],
            "final_memory_mb": final_memory['process_memory_mb']
        }
    
    def _cleanup_temp_files(self) -> int:
        """Clean up temporary files created during processing"""
        cleaned_count = 0
        
        for temp_file in self.temp_files[:]:  # Copy list to avoid modification during iteration
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    cleaned_count += 1
                self.temp_files.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
        
        return cleaned_count
    
    def create_temp_file(self, suffix: str = ".tmp", prefix: str = "hackreporter_") -> Path:
        """Create a temporary file that will be cleaned up automatically"""
        temp_file = Path(tempfile.mktemp(suffix=suffix, prefix=prefix))
        self.temp_files.append(temp_file)
        return temp_file
    
    def optimize_video_file(self, input_path: Path, max_size_mb: int = 100) -> Optional[Path]:
        """
        Optimize a video file for processing by reducing size if needed
        
        Args:
            input_path: Path to input video file
            max_size_mb: Maximum file size in MB
            
        Returns:
            Path to optimized video file (may be original if already small enough)
        """
        file_size_mb = input_path.stat().st_size / (1024 * 1024)
        
        if file_size_mb <= max_size_mb:
            logger.info(f"Video file {input_path.name} is already optimized ({file_size_mb:.1f}MB)")
            return input_path
        
        logger.info(f"Optimizing video file {input_path.name} ({file_size_mb:.1f}MB -> ~{max_size_mb}MB)")
        
        # Create temporary optimized file
        temp_output = self.create_temp_file(suffix=input_path.suffix)
        
        try:
            # Use ffmpeg to optimize the video
            import subprocess
            
            # Calculate target bitrate
            duration = self._get_video_duration(input_path)
            if duration > 0:
                target_bitrate = int((max_size_mb * 8192 * 0.9) / duration)  # 90% for video, 10% for audio
            else:
                target_bitrate = 1000  # Fallback
            
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '28',
                '-b:v', f'{target_bitrate}k',
                '-maxrate', f'{int(target_bitrate * 1.5)}k',
                '-bufsize', f'{int(target_bitrate * 2)}k',
                '-vf', 'scale=-2:720',  # Scale to 720p max height
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y',  # Overwrite output
                str(temp_output)
            ]
            
            result = subprocess.run(cmd, capture_output=True, check=True)
            
            # Check if optimization was successful
            if temp_output.exists():
                new_size_mb = temp_output.stat().st_size / (1024 * 1024)
                logger.info(f"Video optimized: {file_size_mb:.1f}MB -> {new_size_mb:.1f}MB")
                return temp_output
            else:
                logger.error("Video optimization failed - output file not created")
                return input_path
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Video optimization failed: {e}")
            return input_path
        except FileNotFoundError:
            logger.error("ffmpeg not found - video optimization skipped")
            return input_path
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds using ffprobe"""
        try:
            import subprocess
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip()) if result.stdout else 0
        except:
            return 0
    
    def monitor_memory_usage(self, task_name: str, interval: float = 5.0):
        """Context manager for monitoring memory usage during a task"""
        import threading
        import time
        
        class MemoryMonitor:
            def __init__(self, optimizer, task_name, interval):
                self.optimizer = optimizer
                self.task_name = task_name
                self.interval = interval
                self.monitoring = False
                self.thread = None
                self.peak_memory = 0
                
            def start(self):
                self.monitoring = True
                self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self.thread.start()
                
            def stop(self):
                self.monitoring = False
                if self.thread:
                    self.thread.join(timeout=1)
                    
            def _monitor_loop(self):
                while self.monitoring:
                    memory_stats = self.optimizer.get_memory_usage()
                    current_memory = memory_stats['process_memory_mb']
                    
                    if current_memory > self.peak_memory:
                        self.peak_memory = current_memory
                    
                    if self.optimizer.should_cleanup():
                        logger.warning(f"High memory usage detected during {self.task_name}: {current_memory:.1f}MB")
                        self.optimizer.cleanup_memory()
                    
                    time.sleep(self.interval)
        
        monitor = MemoryMonitor(self, task_name, interval)
        monitor.start()
        
        try:
            yield monitor
        finally:
            monitor.stop()
            logger.info(f"Task {task_name} peak memory usage: {monitor.peak_memory:.1f}MB")
    
    def cleanup_all(self):
        """Clean up all resources"""
        self._cleanup_temp_files()
        gc.collect()
        logger.info("Memory optimizer cleanup completed")


# Global memory optimizer instance
memory_optimizer = MemoryOptimizer()