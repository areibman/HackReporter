#!/usr/bin/env python3
"""
Optimized video processing demonstration
Shows performance improvements and monitoring
"""

import asyncio
import time
from pathlib import Path
from performance_monitor import PerformanceMonitor
from performance_config import perf_config

async def optimized_video_processing_demo(video_directory: str):
    """
    Demonstrate optimized video processing with performance monitoring
    """
    print("🚀 Starting Optimized Video Processing Demo")
    print("=" * 50)
    
    # Initialize performance monitoring
    monitor = PerformanceMonitor(monitoring_interval=1.0)
    monitor.start_monitoring()
    
    try:
        # Show system information
        perf_config.print_system_info()
        
        # Check video directory
        video_dir = Path(video_directory)
        if not video_dir.exists():
            print(f"❌ Directory not found: {video_directory}")
            return
            
        # Find video files (simulated)
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        video_files = []
        for ext in video_extensions:
            video_files.extend(video_dir.glob(f'*{ext}'))
            video_files.extend(video_dir.glob(f'*{ext.upper()}'))
            
        if not video_files:
            print(f"📹 No video files found in {video_directory}")
            # Create some dummy files for demo
            print("🎬 Creating demo video files for testing...")
            for i in range(3):
                dummy_file = video_dir / f"demo_video_{i+1}.mp4"
                dummy_file.touch()
                video_files.append(dummy_file)
                
        print(f"📹 Found {len(video_files)} video files")
        
        # Get optimized configuration
        video_config = perf_config.get_video_processing_config(len(video_files))
        cache_config = perf_config.get_cache_config()
        memory_config = perf_config.get_memory_config()
        
        print(f"\n⚙️  Optimization Settings:")
        print(f"   Max Concurrent: {video_config['max_concurrent_videos']}")
        print(f"   Sequential Mode: {video_config['use_sequential']}")
        print(f"   Cache Enabled: {cache_config['enabled']}")
        print(f"   Memory Optimization: {memory_config['enable_gc_optimization']}")
        
        # Simulate optimized processing
        print(f"\n🎬 Processing {len(video_files)} videos...")
        
        if video_config['use_sequential']:
            await _sequential_processing_demo(video_files, video_config)
        else:
            await _parallel_processing_demo(video_files, video_config)
            
        # Show performance results
        print("\n📊 Performance Results:")
        stats = monitor.get_current_stats()
        for key, value in stats.items():
            if value is not None:
                print(f"   {key}: {value}")
                
        # Generate summary and recommendations
        summary = monitor.get_performance_summary()
        print(f"\n📈 Processing Summary:")
        print(f"   Duration: {summary['monitoring_duration_minutes']} minutes")
        print(f"   Average CPU: {summary['cpu_usage']['average']}%")
        print(f"   Peak Memory: {summary['memory_usage']['peak_percent']}%")
        print(f"   Disk I/O: {summary['disk_io']['total_read_mb']:.1f}MB read, {summary['disk_io']['total_write_mb']:.1f}MB written")
        
        print(f"\n💡 Optimization Recommendations:")
        for rec in summary["recommendations"]:
            print(f"   • {rec}")
            
    finally:
        monitor.stop_monitoring()
        monitor.save_metrics("demo_performance_metrics.json")
        
        # Cleanup demo files
        for video_file in video_files:
            if video_file.name.startswith("demo_video_"):
                video_file.unlink(missing_ok=True)

async def _sequential_processing_demo(video_files, config):
    """Simulate sequential processing with optimizations"""
    print("🔄 Using Sequential Processing (optimized for memory)")
    
    for i, video_file in enumerate(video_files, 1):
        print(f"   Processing video {i}/{len(video_files)}: {video_file.name}")
        
        # Simulate video analysis (with optimizations)
        await _simulate_optimized_analysis(video_file)
        
        # Add delay between videos as configured
        if i < len(video_files):
            delay = config.get('api_delay_seconds', 2)
            print(f"   ⏳ Waiting {delay}s (API rate limiting)...")
            await asyncio.sleep(delay)

async def _parallel_processing_demo(video_files, config):
    """Simulate parallel processing with optimizations"""
    max_concurrent = config['max_concurrent_videos']
    print(f"⚡ Using Parallel Processing (max {max_concurrent} concurrent)")
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(video_file, index):
        async with semaphore:
            print(f"   🎬 Starting video {index+1}: {video_file.name}")
            await _simulate_optimized_analysis(video_file)
            print(f"   ✅ Completed video {index+1}: {video_file.name}")
    
    # Process all videos in parallel
    tasks = [
        process_with_limit(video_file, i) 
        for i, video_file in enumerate(video_files)
    ]
    
    await asyncio.gather(*tasks)

async def _simulate_optimized_analysis(video_file):
    """Simulate optimized video analysis with caching and lazy loading"""
    
    # Simulate cache check
    cache_key = f"{video_file.name}_{video_file.stat().st_size if video_file.exists() else 0}"
    
    # 30% chance of cache hit for demo
    import random
    if random.random() < 0.3:
        print(f"      📋 Cache hit for {video_file.name}")
        await asyncio.sleep(0.1)  # Fast cache retrieval
        return
    
    # Simulate lazy loading of heavy dependencies
    print(f"      🔍 Analyzing {video_file.name} (lazy loading optimizations)")
    await asyncio.sleep(1.0)  # Simulate faster processing
    
    # Simulate memory-optimized processing
    print(f"      🧠 Memory-optimized processing")
    await asyncio.sleep(0.5)
    
    # Simulate caching result
    print(f"      💾 Caching result for future use")

def main():
    """Main entry point for demo"""
    import sys
    
    if len(sys.argv) > 1:
        video_directory = sys.argv[1]
    else:
        video_directory = "./test_videos"
        
    # Create test directory if it doesn't exist
    Path(video_directory).mkdir(exist_ok=True)
    
    # Run the demo
    asyncio.run(optimized_video_processing_demo(video_directory))

if __name__ == "__main__":
    main()