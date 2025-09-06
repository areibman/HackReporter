#!/usr/bin/env python
"""
Performance benchmarking tool for HackReporter
Helps identify bottlenecks and optimize settings
"""

import os
import sys
import time
import asyncio
import psutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import statistics
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Benchmark:
    """Run performance benchmarks on the video processing pipeline"""
    
    def __init__(self, test_dir: str):
        self.test_dir = Path(test_dir)
        self.results = []
        self.process = psutil.Process()
        
    def get_system_info(self) -> Dict:
        """Get system information"""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            'memory_total': psutil.virtual_memory().total / (1024**3),  # GB
            'memory_available': psutil.virtual_memory().available / (1024**3),  # GB
            'python_version': sys.version.split()[0]
        }
    
    async def benchmark_configuration(self, config: Dict) -> Dict:
        """Benchmark a specific configuration"""
        # Apply configuration
        for key, value in config.items():
            os.environ[key] = str(value)
        
        # Import after setting environment
        from crew_optimized import process_videos_optimized
        
        # Get initial metrics
        start_time = time.time()
        start_memory = self.process.memory_info().rss / (1024**2)  # MB
        
        try:
            # Run processing
            results = await process_videos_optimized(
                directory=str(self.test_dir),
                attendee_list=None
            )
            
            # Calculate metrics
            end_time = time.time()
            end_memory = self.process.memory_info().rss / (1024**2)
            
            return {
                'config': config,
                'success': True,
                'total_time': end_time - start_time,
                'memory_used': end_memory - start_memory,
                'videos_processed': results.get('processed_videos', 0),
                'errors': []
            }
            
        except Exception as e:
            return {
                'config': config,
                'success': False,
                'total_time': time.time() - start_time,
                'memory_used': 0,
                'videos_processed': 0,
                'errors': [str(e)]
            }
    
    async def run_benchmarks(self) -> List[Dict]:
        """Run multiple benchmark configurations"""
        configurations = [
            {
                'name': 'Sequential',
                'SEQUENTIAL_VIDEO_PROCESSING': 'true',
                'MAX_CONCURRENT_VIDEOS': '1'
            },
            {
                'name': 'Parallel-2',
                'SEQUENTIAL_VIDEO_PROCESSING': 'false',
                'MAX_CONCURRENT_VIDEOS': '2',
                'BATCH_SIZE': '3'
            },
            {
                'name': 'Parallel-3',
                'SEQUENTIAL_VIDEO_PROCESSING': 'false',
                'MAX_CONCURRENT_VIDEOS': '3',
                'BATCH_SIZE': '5'
            },
            {
                'name': 'Parallel-5',
                'SEQUENTIAL_VIDEO_PROCESSING': 'false',
                'MAX_CONCURRENT_VIDEOS': '5',
                'BATCH_SIZE': '10'
            },
            {
                'name': 'LowFPS',
                'SEQUENTIAL_VIDEO_PROCESSING': 'false',
                'MAX_CONCURRENT_VIDEOS': '3',
                'DEFAULT_FPS': '0.25'
            },
            {
                'name': 'HighFPS',
                'SEQUENTIAL_VIDEO_PROCESSING': 'false',
                'MAX_CONCURRENT_VIDEOS': '3',
                'DEFAULT_FPS': '1.0'
            }
        ]
        
        results = []
        
        for config in configurations:
            print(f"\n📊 Running benchmark: {config['name']}")
            print("-" * 40)
            
            result = await self.benchmark_configuration(config)
            result['name'] = config['name']
            results.append(result)
            
            if result['success']:
                if result['videos_processed'] > 0:
                    avg_time = result['total_time'] / result['videos_processed']
                    print(f"✅ Success - Time: {result['total_time']:.2f}s, "
                          f"Avg: {avg_time:.2f}s/video, "
                          f"Memory: {result['memory_used']:.1f}MB")
                else:
                    print(f"⚠️  No videos processed")
            else:
                print(f"❌ Failed: {result['errors'][0]}")
            
            # Clean up between runs
            import gc
            gc.collect()
            await asyncio.sleep(5)  # Cool down period
        
        return results
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze benchmark results and provide recommendations"""
        successful_runs = [r for r in results if r['success'] and r['videos_processed'] > 0]
        
        if not successful_runs:
            return {'error': 'No successful benchmark runs'}
        
        # Find best configurations
        fastest = min(successful_runs, key=lambda x: x['total_time'])
        most_efficient = min(successful_runs, key=lambda x: x['total_time'] / x['videos_processed'])
        least_memory = min(successful_runs, key=lambda x: x['memory_used'])
        
        # Calculate statistics
        times = [r['total_time'] for r in successful_runs]
        memories = [r['memory_used'] for r in successful_runs]
        
        analysis = {
            'fastest': {
                'name': fastest['name'],
                'time': fastest['total_time'],
                'config': fastest['config']
            },
            'most_efficient': {
                'name': most_efficient['name'],
                'time_per_video': most_efficient['total_time'] / most_efficient['videos_processed'],
                'config': most_efficient['config']
            },
            'least_memory': {
                'name': least_memory['name'],
                'memory': least_memory['memory_used'],
                'config': least_memory['config']
            },
            'statistics': {
                'avg_time': statistics.mean(times),
                'std_time': statistics.stdev(times) if len(times) > 1 else 0,
                'avg_memory': statistics.mean(memories),
                'std_memory': statistics.stdev(memories) if len(memories) > 1 else 0
            }
        }
        
        # Generate recommendations
        recommendations = []
        
        if fastest['name'] == most_efficient['name']:
            recommendations.append(f"Use '{fastest['name']}' configuration for best overall performance")
        else:
            recommendations.append(f"Use '{fastest['name']}' for fastest processing")
            recommendations.append(f"Use '{most_efficient['name']}' for best efficiency")
        
        if least_memory['memory_used'] < 500:
            recommendations.append(f"'{least_memory['name']}' is best for low-memory systems")
        
        # Check if parallel processing helps
        seq_run = next((r for r in successful_runs if r['name'] == 'Sequential'), None)
        par_runs = [r for r in successful_runs if 'Parallel' in r['name']]
        
        if seq_run and par_runs:
            best_parallel = min(par_runs, key=lambda x: x['total_time'])
            speedup = seq_run['total_time'] / best_parallel['total_time']
            if speedup > 1.5:
                recommendations.append(f"Parallel processing provides {speedup:.1f}x speedup")
            else:
                recommendations.append("Consider sequential processing - minimal parallel benefit")
        
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def save_results(self, results: List[Dict], analysis: Dict):
        """Save benchmark results to file"""
        output_dir = Path('output/benchmarks')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'benchmark_{timestamp}.json'
        
        data = {
            'timestamp': timestamp,
            'system_info': self.get_system_info(),
            'test_directory': str(self.test_dir),
            'results': results,
            'analysis': analysis
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Also create a summary report
        report_file = output_dir / f'benchmark_report_{timestamp}.txt'
        with open(report_file, 'w') as f:
            f.write("HACKREPORTER PERFORMANCE BENCHMARK REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Date: {timestamp}\n")
            f.write(f"Test Directory: {self.test_dir}\n\n")
            
            f.write("SYSTEM INFO:\n")
            f.write("-" * 30 + "\n")
            for key, value in self.get_system_info().items():
                f.write(f"{key}: {value}\n")
            
            f.write("\n\nBENCHMARK RESULTS:\n")
            f.write("-" * 30 + "\n")
            for result in results:
                f.write(f"\n{result['name']}:\n")
                if result['success']:
                    f.write(f"  Time: {result['total_time']:.2f}s\n")
                    f.write(f"  Memory: {result['memory_used']:.1f}MB\n")
                    f.write(f"  Videos: {result['videos_processed']}\n")
                else:
                    f.write(f"  FAILED: {result['errors'][0]}\n")
            
            f.write("\n\nANALYSIS & RECOMMENDATIONS:\n")
            f.write("-" * 30 + "\n")
            if 'error' not in analysis:
                f.write(f"Fastest: {analysis['fastest']['name']} "
                       f"({analysis['fastest']['time']:.2f}s)\n")
                f.write(f"Most Efficient: {analysis['most_efficient']['name']} "
                       f"({analysis['most_efficient']['time_per_video']:.2f}s/video)\n")
                f.write(f"Least Memory: {analysis['least_memory']['name']} "
                       f"({analysis['least_memory']['memory']:.1f}MB)\n")
                
                f.write("\nRecommendations:\n")
                for rec in analysis['recommendations']:
                    f.write(f"  • {rec}\n")
            else:
                f.write(f"Error: {analysis['error']}\n")
        
        print(f"📄 Report saved to: {report_file}")


async def main():
    parser = argparse.ArgumentParser(description='Benchmark HackReporter performance')
    parser.add_argument('directory',
                        help='Directory containing test videos',
                        nargs='?',
                        default='.')
    parser.add_argument('--quick', '-q',
                        action='store_true',
                        help='Run quick benchmark (fewer configurations)')
    
    args = parser.parse_args()
    
    # Validate directory
    test_dir = Path(args.directory)
    if not test_dir.exists() or not test_dir.is_dir():
        print(f"❌ Error: '{args.directory}' is not a valid directory")
        sys.exit(1)
    
    # Check for videos
    video_files = list(test_dir.glob('*.mp4')) + list(test_dir.glob('*.mov'))
    if not video_files:
        print(f"❌ No video files found in '{args.directory}'")
        sys.exit(1)
    
    print("🏁 HACKREPORTER PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"Test directory: {test_dir}")
    print(f"Video files: {len(video_files)}")
    print(f"Total size: {sum(f.stat().st_size for f in video_files) / (1024**2):.1f}MB")
    print()
    
    # Check API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not set in environment")
        sys.exit(1)
    
    # Run benchmarks
    benchmark = Benchmark(test_dir)
    
    print("Starting benchmarks... This may take several minutes.\n")
    
    try:
        results = await benchmark.run_benchmarks()
        
        print("\n" + "=" * 60)
        print("📊 BENCHMARK COMPLETE")
        print("=" * 60)
        
        # Analyze results
        analysis = benchmark.analyze_results(results)
        
        if 'error' not in analysis:
            print("\n🏆 BEST CONFIGURATIONS:")
            print(f"  Fastest: {analysis['fastest']['name']} "
                  f"({analysis['fastest']['time']:.2f}s)")
            print(f"  Most Efficient: {analysis['most_efficient']['name']} "
                  f"({analysis['most_efficient']['time_per_video']:.2f}s/video)")
            print(f"  Least Memory: {analysis['least_memory']['name']} "
                  f"({analysis['least_memory']['memory']:.1f}MB)")
            
            print("\n💡 RECOMMENDATIONS:")
            for rec in analysis['recommendations']:
                print(f"  • {rec}")
        else:
            print(f"\n❌ {analysis['error']}")
        
        # Save results
        benchmark.save_results(results, analysis)
        
    except KeyboardInterrupt:
        print("\n⚠️  Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())