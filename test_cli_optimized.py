#!/usr/bin/env python
"""
Optimized CLI tool for HackReporter with performance monitoring and improvements
"""
import argparse
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import asyncio
import time
import psutil
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional

# Import the optimized crew module
try:
    from crew_optimized import process_videos_optimized
except ImportError:
    from crew import process_videos
    process_videos_optimized = process_videos

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Track and report performance metrics"""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {
            'start_memory': 0,
            'peak_memory': 0,
            'end_memory': 0,
            'total_time': 0,
            'videos_processed': 0,
            'videos_failed': 0,
            'api_calls': 0
        }
        self.process = psutil.Process()
        
    def start(self):
        """Start tracking performance"""
        self.start_time = time.time()
        self.metrics['start_memory'] = self.process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"Starting memory usage: {self.metrics['start_memory']:.1f}MB")
        
    def update_memory(self):
        """Update peak memory usage"""
        current_memory = self.process.memory_info().rss / 1024 / 1024
        self.metrics['peak_memory'] = max(self.metrics['peak_memory'], current_memory)
        
    def stop(self, results: Dict):
        """Stop tracking and calculate final metrics"""
        self.metrics['end_memory'] = self.process.memory_info().rss / 1024 / 1024
        self.metrics['total_time'] = time.time() - self.start_time
        
        # Extract results metrics
        if 'processed_videos' in results:
            self.metrics['videos_processed'] = results['processed_videos']
        
        # Count failures
        if 'individual_results' in results:
            for result in results['individual_results']:
                if isinstance(result, Exception) or (isinstance(result, str) and result.startswith("Error")):
                    self.metrics['videos_failed'] += 1
        
        return self.metrics
    
    def print_report(self):
        """Print performance report"""
        print("\n" + "="*60)
        print("📊 PERFORMANCE REPORT")
        print("="*60)
        print(f"⏱️  Total Time: {self.metrics['total_time']:.2f} seconds")
        print(f"📹 Videos Processed: {self.metrics['videos_processed']}")
        if self.metrics['videos_failed'] > 0:
            print(f"❌ Videos Failed: {self.metrics['videos_failed']}")
        
        if self.metrics['videos_processed'] > 0:
            avg_time = self.metrics['total_time'] / self.metrics['videos_processed']
            print(f"⚡ Average Time per Video: {avg_time:.2f} seconds")
        
        print(f"\n💾 Memory Usage:")
        print(f"   Start: {self.metrics['start_memory']:.1f}MB")
        print(f"   Peak:  {self.metrics['peak_memory']:.1f}MB")
        print(f"   End:   {self.metrics['end_memory']:.1f}MB")
        print(f"   Growth: {self.metrics['end_memory'] - self.metrics['start_memory']:.1f}MB")
        
        # Performance grade
        grade = self._calculate_grade()
        print(f"\n🎯 Performance Grade: {grade}")
        print("="*60)
        
    def _calculate_grade(self) -> str:
        """Calculate performance grade based on metrics"""
        if self.metrics['videos_processed'] == 0:
            return "N/A"
        
        avg_time = self.metrics['total_time'] / self.metrics['videos_processed']
        memory_growth = self.metrics['end_memory'] - self.metrics['start_memory']
        failure_rate = self.metrics['videos_failed'] / self.metrics['videos_processed']
        
        score = 100
        
        # Time penalty (target: < 30s per video)
        if avg_time > 60:
            score -= 20
        elif avg_time > 30:
            score -= 10
        
        # Memory penalty (target: < 500MB growth)
        if memory_growth > 1000:
            score -= 20
        elif memory_growth > 500:
            score -= 10
        
        # Failure penalty
        score -= failure_rate * 30
        
        if score >= 90:
            return "A+ (Excellent)"
        elif score >= 80:
            return "A (Very Good)"
        elif score >= 70:
            return "B (Good)"
        elif score >= 60:
            return "C (Fair)"
        else:
            return "D (Needs Improvement)"
    
    def save_metrics(self, output_dir: Path):
        """Save metrics to JSON file"""
        metrics_file = output_dir / f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        logger.info(f"Metrics saved to {metrics_file}")


def optimize_environment():
    """Set optimal environment variables for performance"""
    optimizations = {
        'MAX_CONCURRENT_VIDEOS': os.getenv('MAX_CONCURRENT_VIDEOS', '3'),
        'BATCH_SIZE': os.getenv('BATCH_SIZE', '5'),
        'BATCH_DELAY': os.getenv('BATCH_DELAY', '10'),
        'MAX_RETRIES': os.getenv('MAX_RETRIES', '2'),
        'RETRY_DELAY': os.getenv('RETRY_DELAY', '5'),
        'MAX_VIDEO_SIZE_MB': os.getenv('MAX_VIDEO_SIZE_MB', '500'),
        'VERBOSE': os.getenv('VERBOSE', 'false'),
        'DEBUG_MODE': os.getenv('DEBUG_MODE', 'false')
    }
    
    # Apply optimizations
    for key, value in optimizations.items():
        os.environ[key] = value
    
    return optimizations


def check_video_sizes(video_dir: Path) -> Dict:
    """Check video file sizes and provide optimization recommendations"""
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    video_files = []
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f'*{ext}'))
        video_files.extend(video_dir.glob(f'*{ext.upper()}'))
    
    total_size = 0
    large_files = []
    
    for vf in video_files:
        size_mb = vf.stat().st_size / (1024 * 1024)
        total_size += size_mb
        if size_mb > 50:
            large_files.append((vf.name, size_mb))
    
    return {
        'total_files': len(video_files),
        'total_size_mb': total_size,
        'large_files': large_files,
        'avg_size_mb': total_size / len(video_files) if video_files else 0
    }


async def run_with_monitoring(video_dir: Path, attendees: Optional[str] = None) -> Dict:
    """Run video processing with performance monitoring"""
    tracker = PerformanceTracker()
    tracker.start()
    
    # Create monitoring task
    async def monitor_memory():
        while True:
            tracker.update_memory()
            await asyncio.sleep(5)  # Update every 5 seconds
    
    monitor_task = asyncio.create_task(monitor_memory())
    
    try:
        # Run the optimized processing
        results = await process_videos_optimized(
            directory=str(video_dir),
            attendee_list=attendees
        )
        
        # Stop monitoring
        monitor_task.cancel()
        
        # Calculate final metrics
        tracker.stop(results)
        
        return results, tracker
        
    except Exception as e:
        monitor_task.cancel()
        tracker.stop({'error': str(e)})
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Optimized HackReporter CLI with performance monitoring'
    )
    parser.add_argument('directory',
                        help='Directory containing video files to process',
                        nargs='?',
                        default='.')
    parser.add_argument('--attendees', '-a',
                        help='Path to attendee list file (optional)',
                        default=None)
    parser.add_argument('--list', '-l',
                        action='store_true',
                        help='List videos in directory without processing')
    parser.add_argument('--optimize', '-o',
                        action='store_true',
                        help='Run video optimization before processing')
    parser.add_argument('--sequential', '-s',
                        action='store_true',
                        help='Process videos sequentially (slower but uses less memory)')
    parser.add_argument('--max-concurrent', '-m',
                        type=int,
                        default=3,
                        help='Maximum concurrent video processing (default: 3)')
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--profile', '-p',
                        action='store_true',
                        help='Enable performance profiling')
    
    args = parser.parse_args()
    
    # Set environment based on arguments
    if args.sequential:
        os.environ['SEQUENTIAL_VIDEO_PROCESSING'] = 'true'
    if args.verbose:
        os.environ['VERBOSE'] = 'true'
        logging.getLogger().setLevel(logging.DEBUG)
    if args.max_concurrent:
        os.environ['MAX_CONCURRENT_VIDEOS'] = str(args.max_concurrent)
    
    # Validate directory
    video_dir = Path(args.directory)
    if not video_dir.exists():
        print(f"❌ Error: Directory '{args.directory}' does not exist")
        sys.exit(1)
    
    if not video_dir.is_dir():
        print(f"❌ Error: '{args.directory}' is not a directory")
        sys.exit(1)
    
    # Check video files and sizes
    size_info = check_video_sizes(video_dir)
    
    if size_info['total_files'] == 0:
        print(f"❌ No video files found in '{args.directory}'")
        sys.exit(1)
    
    print(f"📹 Found {size_info['total_files']} video(s) - Total size: {size_info['total_size_mb']:.1f}MB")
    print(f"   Average size: {size_info['avg_size_mb']:.1f}MB per video")
    
    if size_info['large_files']:
        print(f"\n⚠️  Large files detected (>50MB):")
        for name, size in size_info['large_files'][:5]:  # Show top 5
            print(f"   - {name}: {size:.1f}MB")
        
        if args.optimize or (not args.list and input("\n❓ Optimize videos before processing? (y/n): ").lower() == 'y'):
            print("\n🔧 Running video optimization...")
            from optimize_videos import optimize_videos_directory
            optimize_videos_directory(str(video_dir))
            # Update video_dir to optimized directory
            video_dir = video_dir.parent / f"{video_dir.name}_optimized"
            if not video_dir.exists():
                print("❌ Optimization failed")
                sys.exit(1)
    
    if args.list:
        # Just list files and exit
        for vf in sorted(video_dir.glob('*.mp4')) + sorted(video_dir.glob('*.mov')):
            size_mb = vf.stat().st_size / (1024 * 1024)
            print(f"   - {vf.name} ({size_mb:.1f}MB)")
        return
    
    # Check required environment variables
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        sys.exit(1)
    
    # Apply performance optimizations
    print("\n⚙️  Applying performance optimizations...")
    optimizations = optimize_environment()
    
    if args.verbose:
        print("Optimization settings:")
        for key, value in optimizations.items():
            print(f"   {key}: {value}")
    
    print(f"\n🚀 Starting optimized processing of {size_info['total_files']} video(s)")
    print("="*60 + "\n")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Run with performance monitoring
        results, tracker = asyncio.run(run_with_monitoring(video_dir, args.attendees))
        
        # Display results
        print("\n" + "="*60)
        print("✅ Processing Complete!")
        print("="*60 + "\n")
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
        else:
            print(f"📊 Successfully processed {results['processed_videos']} videos")
            print(f"\n📝 Output saved to: output/tweet_thread.md")
            
            # Show preview
            output_file = Path("output/tweet_thread.md")
            if output_file.exists():
                print("\n--- Preview of tweet thread ---")
                content = output_file.read_text()
                lines = content.split('\n')[:10]
                preview = '\n'.join(lines)
                if len(content) > len(preview):
                    preview += "\n... (truncated)"
                print(preview)
        
        # Print performance report
        tracker.print_report()
        
        # Save metrics if profiling enabled
        if args.profile:
            tracker.save_metrics(output_dir)
            print(f"\n📈 Performance metrics saved to output/")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Processing failed")
        sys.exit(1)


if __name__ == "__main__":
    main()