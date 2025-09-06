"""
Performance configuration settings for HackReporter
Optimizes resource usage based on system capabilities
"""

import os
import psutil
from pathlib import Path
from typing import Dict, Any

class PerformanceConfig:
    """Dynamic performance configuration based on system resources"""
    
    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        self.disk_free_gb = psutil.disk_usage('/').free / (1024**3)
        
    def get_video_processing_config(self, video_count: int = 1) -> Dict[str, Any]:
        """Get optimized configuration for video processing"""
        
        # Calculate optimal concurrent videos
        max_concurrent = min(
            max(1, self.cpu_count // 2),  # Use half of CPU cores
            max(1, int(self.memory_gb // 4)),  # 4GB per concurrent video
            video_count,  # Don't exceed video count
            3  # Cap at 3 to avoid API quota issues
        )
        
        # Calculate chunk sizes for batch processing
        chunk_size = min(10, max(1, video_count // max_concurrent))
        
        # Determine if we should use sequential processing
        use_sequential = (
            self.memory_gb < 8 or  # Low memory systems
            video_count > 10 or    # Many videos
            os.getenv("SEQUENTIAL_VIDEO_PROCESSING", "false").lower() == "true"
        )
        
        return {
            'max_concurrent_videos': max_concurrent,
            'chunk_size': chunk_size,
            'use_sequential': use_sequential,
            'cache_enabled': self.disk_free_gb > 5,  # Enable cache if >5GB free
            'memory_optimization': self.memory_gb < 16,  # Enable for <16GB systems
            'api_delay_seconds': 2 if use_sequential else 1,
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration based on available disk space"""
        
        cache_dir = Path(".cache")
        max_cache_size_gb = min(5, max(0.5, self.disk_free_gb * 0.1))  # 10% of free space, max 5GB
        
        return {
            'enabled': self.disk_free_gb > 2,  # Disable if <2GB free
            'max_size_gb': max_cache_size_gb,
            'cache_dir': cache_dir,
            'ttl_hours': 24,  # Cache results for 24 hours
        }
    
    def get_memory_config(self) -> Dict[str, Any]:
        """Get memory optimization settings"""
        
        return {
            'enable_gc_optimization': self.memory_gb < 16,
            'chunk_processing': self.memory_gb < 8,
            'lazy_imports': True,  # Always use lazy imports
            'result_streaming': self.memory_gb < 12,  # Stream results for low memory
        }
    
    def print_system_info(self):
        """Print system information for debugging"""
        print(f"🖥️  System Resources:")
        print(f"   CPU Cores: {self.cpu_count}")
        print(f"   RAM: {self.memory_gb:.1f}GB")
        print(f"   Free Disk: {self.disk_free_gb:.1f}GB")
        
        video_config = self.get_video_processing_config()
        print(f"📊 Performance Settings:")
        print(f"   Max Concurrent Videos: {video_config['max_concurrent_videos']}")
        print(f"   Sequential Mode: {video_config['use_sequential']}")
        print(f"   Cache Enabled: {video_config['cache_enabled']}")
        print(f"   Memory Optimization: {video_config['memory_optimization']}")

# Global instance
perf_config = PerformanceConfig()