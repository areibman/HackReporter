# server.py
from fastmcp import FastMCP
from hackreporter import HackReporterCrew
import os
import sys
from pathlib import Path

# Add src to Python path for imports - MUST be before local imports
sys.path.append(str(Path(__file__).parent / "src"))

# Now we can import our local modules


mcp = FastMCP(name="HackReporter")


@mcp.tool
def kickoff_hackathon_reporter(directory: str, attendee_list: str | None = None) -> str:
    """
    Given a directory path, kick off the hackathon reporter.
    The directory path should contain several video files.
    Optional: provide a path to an attendee list file.
    """
    print(f"Kicking off hackathon reporter for directory: {directory}")

    # Validate directory exists
    if not os.path.exists(directory):
        return f"Error: Directory '{directory}' does not exist"

    if not os.path.isdir(directory):
        return f"Error: '{directory}' is not a directory"

    # Validate attendee list if provided
    if attendee_list and not os.path.exists(attendee_list):
        return f"Warning: Attendee list file '{attendee_list}' not found, proceeding without it"

    try:
        # Initialize the HackReporter crew
        crew = HackReporterCrew()

        # Process all videos in the directory
        results = crew.process_videos(directory, attendee_list)

        # Format results for output
        if "error" in results:
            return results["error"]

        output = f"Successfully processed {results['processed_videos']} videos!\n\n"

        for video_result in results['results']:
            output += f"Video: {video_result['video']}\n"
            output += f"Result: {video_result['result']}\n"
            output += "-" * 50 + "\n\n"

        output += f"Tweet threads have been saved to the output/ directory."

        return output

    except Exception as e:
        return f"Error running HackReporter crew: {str(e)}"


@mcp.tool
def create_tweet_thread(tweet_file: str) -> str:
    """
    Create a tweet thread in Typefully API from the generated tweet file.

    Args:
        tweet_file: Path to the markdown file containing the tweet thread
    """
    # TODO: Implement Typefully API integration
    # Reference: https://support.typefully.com/en/articles/8718287-typefully-api

    return f"Tweet thread creation from '{tweet_file}' is not yet implemented. Please check the Typefully API documentation."


if __name__ == "__main__":
    mcp.run()
