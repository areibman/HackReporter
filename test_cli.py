#!/usr/bin/env python
"""
CLI tool for testing HackReporter video processing
"""
import argparse
import sys
from pathlib import Path
from crew import process_videos
import os
from dotenv import load_dotenv
import agentops
import weave
import asyncio

# Load environment variables
load_dotenv()

# Initialize AgentOps with auto_start_session=False
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY", "YOUR_API_KEY")
agentops.init(api_key=AGENTOPS_API_KEY,
              auto_start_session=False,
              tags=["hackathon", "video-processing", "cli"])
# weave.init('HackReporter')


def main():
    parser = argparse.ArgumentParser(description='Process hackathon videos and generate tweet threads')
    parser.add_argument('directory',
                        help='Directory containing video files to process',
                        nargs='?',
                        default='/Users/reibs/Projects/HackReporter/short_tests')
    parser.add_argument('--attendees', '-a',
                        help='Path to attendee list file (optional)',
                        default=None)
    parser.add_argument('--list', '-l',
                        action='store_true',
                        help='List videos in directory without processing')

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
    for vf in sorted(video_files):
        size_mb = vf.stat().st_size / (1024 * 1024)
        print(f"   - {vf.name} ({size_mb:.1f}MB)")

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
    print(f"\n🚀 Ready to process {len(video_files)} video(s)")

    print("\n" + "="*50)
    print("Starting HackReporter crew...")
    print("="*50 + "\n")

    # Start AgentOps trace
    tracer = None
    try:
        tracer = agentops.start_trace(
            trace_name=f"CLI HackReporter - {video_dir.name}",
            tags=["cli", "video-processing", str(video_dir)]
        )

        # Process videos with a timeout
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Crew execution timed out after 5 minutes")

        # Set a 5-minute timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(300)  # 5 minutes

        try:
            results = asyncio.run(process_videos(
                directory=str(video_dir),
                attendee_list=args.attendees
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
        if tracer:
            agentops.end_trace(tracer, end_state="Timeout")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if tracer:
            agentops.end_trace(tracer, end_state="Fail")
        sys.exit(1)
    finally:
        # Ensure AgentOps is properly shut down
        agentops.end_all_sessions()


if __name__ == "__main__":
    main()
