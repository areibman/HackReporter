#!/usr/bin/env python
"""
Optimized CLI tool for testing HackReporter video processing with performance monitoring
"""
import argparse
import sys
from pathlib import Path
from crew import process_videos_optimized
import os
from dotenv import load_dotenv
import agentops
import asyncio
import logging
from performance_monitor import performance_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize AgentOps with auto_start_session=False
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY", "YOUR_API_KEY")
agentops.init(api_key=AGENTOPS_API_KEY,
              auto_start_session=False,
              tags=["hackathon", "video-processing", "cli", "optimized"])


def main():
    parser = argparse.ArgumentParser(description='Process hackathon videos with optimized performance')
    parser.add_argument('directory',
                        help='Directory containing video files to process',
                        nargs='?',
                        default='/Users/reibs/Projects/HackReporter/short_tests_optimized')
    parser.add_argument('--attendees', '-a',
                        help='Path to attendee list file (optional)',
                        default=None)
    parser.add_argument('--list', '-l',
                        action='store_true',
                        help='List videos in directory without processing')
    parser.add_argument('--url', '-u',
                        help='URL of hackathon project gallery (e.g., devpost) to scrape for team information',
                        default=None)
    parser.add_argument('--performance-report', '-p',
                        help='Path to save performance report (default: output/performance_report.json)',
                        default='output/performance_report.json')
    parser.add_argument('--max-concurrent', '-c',
                        type=int,
                        default=2,
                        help='Maximum concurrent video processing tasks (default: 2)')
    parser.add_argument('--timeout', '-t',
                        type=int,
                        default=1800,
                        help='Timeout in seconds for video processing (default: 1800)')

    args = parser.parse_args()

    # Validate directory
    video_dir = Path(args.directory)
    if not video_dir.exists():
        print(f"❌ Error: Directory '{args.directory}' does not exist")
        sys.exit(1)

    if not video_dir.is_dir():
        print(f"❌ Error: '{args.directory}' is not a directory")
        sys.exit(1)

    # Find video files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    video_files = []
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f'*{ext}'))
        video_files.extend(video_dir.glob(f'*{ext.upper()}'))

    if not video_files:
        print(f"❌ No video files found in '{args.directory}'")
        sys.exit(1)

    print(f"📹 Found {len(video_files)} video(s) in '{args.directory}':")
    total_size = 0
    for vf in sorted(video_files):
        size_mb = vf.stat().st_size / (1024 * 1024)
        total_size += size_mb
        print(f"   - {vf.name} ({size_mb:.1f}MB)")
    
    print(f"📊 Total size: {total_size:.1f}MB")

    if args.list:
        # Just list files and exit
        return

    # Check for required environment variables
    required_vars = ['GOOGLE_API_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"\n⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Make sure to set these in your .env file")

    # Prompt to continue
    print(f"\n🚀 Ready to process {len(video_files)} video(s) with optimized performance")
    print(f"⚙️  Configuration:")
    print(f"   - Max concurrent tasks: {args.max_concurrent}")
    print(f"   - Timeout: {args.timeout}s")
    print(f"   - Performance report: {args.performance_report}")

    print("\n" + "="*50)
    print("Starting Optimized HackReporter crew...")
    print("="*50 + "\n")

    # Start AgentOps trace
    tracer = None
    try:
        tracer = agentops.start_trace(
            trace_name=f"Optimized CLI HackReporter - {video_dir.name}",
            tags=["cli", "video-processing", "optimized", str(video_dir)]
        )

        # Process videos with timeout
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(f"Processing timed out after {args.timeout} seconds")

        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.timeout)

        try:
            results = asyncio.run(process_videos_optimized(
                directory=str(video_dir),
                attendee_list=args.attendees,
            ))
        finally:
            # Cancel the alarm
            signal.alarm(0)

        # Display results
        print("\n" + "="*50)
        print("✅ Processing Complete!")
        print("="*50 + "\n")

        if "error" in results:
            print(f"❌ Error: {results['error']}")
            if tracer:
                agentops.end_trace(tracer, end_state="Fail")
        else:
            print(f"📊 Processed {results['processed_videos']} videos")
            print(f"\n📝 Output saved to: output/tweet_thread.md")

            # Show performance summary if available
            if 'performance_summary' in results:
                perf = results['performance_summary']
                print(f"\n📈 Performance Summary:")
                print(f"   - Total time: {perf.get('monitoring_duration', 0):.2f}s")
                print(f"   - Success rate: {perf.get('tasks', {}).get('success_rate', 0)*100:.1f}%")
                print(f"   - Peak memory: {perf.get('memory', {}).get('peak_mb', 0):.1f}MB")
                print(f"   - Peak CPU: {perf.get('cpu', {}).get('peak_percent', 0):.1f}%")

            # Show a preview of the output if it exists
            output_file = Path("output/tweet_thread.md")
            if output_file.exists():
                print("\n--- Preview of tweet thread ---")
                content = output_file.read_text()
                # Show first 500 chars or first 10 lines
                lines = content.split('\n')[:10]
                preview = '\n'.join(lines)
                if len(content) > len(preview):
                    preview += "\n... (truncated)"
                print(preview)

            if tracer:
                agentops.end_trace(tracer, end_state="Success")

    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        if tracer:
            agentops.end_trace(tracer, end_state="Cancelled")
        sys.exit(1)
    except TimeoutError as e:
        print(f"\n⏱️  {str(e)}")
        print("The crew is taking too long. This often happens when:")
        print("- The agent is not iterating through all videos properly")
        print("- There's an issue with context passing between tasks")
        print("- API rate limits are being hit")
        if tracer:
            agentops.end_trace(tracer, end_state="Timeout")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Unexpected error during processing")
        if tracer:
            agentops.end_trace(tracer, end_state="Fail")
        sys.exit(1)
    finally:
        # Ensure AgentOps is properly shut down
        agentops.end_all_sessions()


if __name__ == "__main__":
    main()