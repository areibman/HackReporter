# server.py
from fastmcp import FastMCP
from crew import HackReporterCrew
import agentops
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# IMPORTANT: Import and initialize AgentOps BEFORE importing CrewAI

# Initialize AgentOps with auto_start_session=False for manual session management
# Replace with your actual API key or use environment variable
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY", "YOUR_API_KEY")
agentops.init(api_key=AGENTOPS_API_KEY,
              auto_start_session=False,
              tags=["hackathon", "video-processing"])

# Now import CrewAI after AgentOps is initialized


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

    # Start an AgentOps trace for this workflow
    tracer = agentops.start_trace(
        trace_name=f"HackReporter Processing - {os.path.basename(directory)}",
        tags=["video-processing", "hackathon", directory]
    )

    print("Starting hackathon reporter crew")

    try:
        # Initialize the HackReporter crew
        crew = HackReporterCrew()

        # Process all videos in the directory
        results = crew.process_videos(directory, attendee_list)

        # Format results for output
        if "error" in results:
            # End trace with failure state
            agentops.end_trace(tracer, end_state="Fail")
            return results["error"]

        output = f"Successfully processed {results['processed_videos']} videos!\n\n"

        output += "Videos processed:\n"
        for video_file in results['video_files']:
            output += f"  - {video_file}\n"

        output += f"\nResult:\n{results['result']}\n\n"
        output += f"Tweet thread has been saved to the output/ directory."

        # End trace with success state
        agentops.end_trace(tracer, end_state="Success")
        return output

    except Exception as e:
        # End trace with failure state on any exception
        if tracer:
            agentops.end_trace(tracer, end_state="Fail")
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
