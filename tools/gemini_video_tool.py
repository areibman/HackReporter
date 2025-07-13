from crewai.tools import BaseTool
from typing import Type, Any, Optional, Dict
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import os
import time
from pathlib import Path


class GeminiVideoToolInput(BaseModel):
    """Input schema for GeminiVideoTool."""
    video_path: str = Field(description="Path to the video file to analyze")
    prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for video analysis"
    )
    start_time: Optional[str] = Field(
        default=None,
        description="Start time for video clip in MM:SS format (e.g., '01:30')"
    )
    end_time: Optional[str] = Field(
        default=None,
        description="End time for video clip in MM:SS format (e.g., '02:45')"
    )
    fps: Optional[float] = Field(
        default=1.0,
        description="Frames per second to sample (default: 1 FPS)"
    )
    transcribe: bool = Field(
        default=False,
        description="Whether to transcribe audio with timestamps"
    )


class GeminiVideoTool(BaseTool):
    name: str = "gemini_video_analyzer"
    description: str = (
        "Analyzes video content using Google's Gemini API to extract insights, "
        "summaries, transcriptions, and key information from hackathon project demonstrations. "
        "Optimized for large video files (>20MB). Supports video clipping, custom FPS, and timestamped transcription."
    )
    args_schema: Type[BaseModel] = GeminiVideoToolInput

    def _run(
        self,
        video_path: str,
        prompt: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        fps: Optional[float] = 1.0,
        transcribe: bool = False
    ) -> str:
        """
        Analyze a video using Gemini API with advanced video understanding features.
        Optimized for large video files using the File API.

        Args:
            video_path: Path to the video file
            prompt: Custom prompt for analysis
            start_time: Start time for video clip (MM:SS format)
            end_time: End time for video clip (MM:SS format)
            fps: Frames per second to sample
            transcribe: Whether to transcribe audio with timestamps

        Returns:
            Analysis results as a string
        """
        try:
            # Configure Gemini API
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return "Error: GOOGLE_API_KEY environment variable not set"

            # Create client
            client = genai.Client(api_key=api_key)

            # Get file size for metadata
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB

            # Prepare the analysis prompt
            if transcribe:
                analysis_prompt = (
                    "Transcribe the audio from this video, giving timestamps for salient events. "
                    "Also provide visual descriptions of what's happening at key moments. "
                )
            else:
                analysis_prompt = ""

            # Add custom prompt or default hackathon analysis
            if prompt:
                analysis_prompt += prompt
            else:
                analysis_prompt += (
                    "Analyze this hackathon project video and provide:\n"
                    "1. Project name and what it does\n"
                    "2. Key technical innovations and features\n"
                    "3. Team members (if mentioned or shown)\n"
                    "4. Most impressive technical achievements\n"
                    "5. Potential use cases and impact\n"
                    "6. A tweet-style summary (280 chars max)\n"
                    "7. Key timestamps of important moments\n"
                    "8. Any technical challenges mentioned\n"
                    "9. Demo highlights and visual elements"
                )

            # Add metadata to prompt if clipping or custom FPS specified
            if start_time or end_time:
                analysis_prompt += f"\n\nPlease focus on the video segment from {start_time or 'start'} to {end_time or 'end'}."
            if fps != 1.0:
                analysis_prompt += f"\n\nNote: The video is sampled at {fps} FPS for this analysis."

            print(f"Uploading video file ({file_size:.1f}MB) using File API...")

            # Upload the video file
            video_file = client.files.upload(file=video_path)

            # Wait for file to be processed
            print("Waiting for video to be processed...")
            while video_file.state == "PROCESSING":
                time.sleep(2)
                video_file = client.files.get(name=video_file.name)

            if video_file.state == "FAILED":
                return f"Error: Video processing failed - {video_file.state}"

            print("Video processed successfully. Generating analysis...")

            # Create content with uploaded file
            contents = [
                types.Part.from_uri(
                    file_uri=video_file.uri,
                    mime_type=self._get_mime_type(video_path)
                ),
                types.Part.from_text(text=analysis_prompt)
            ]

            # Generate analysis
            response = client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=contents,
                config=types.GenerateContentConfig()
            )

            # Clean up uploaded file
            print("Cleaning up uploaded file...")
            client.files.delete(name=video_file.name)

            # Format the response
            result = response.text

            # Add metadata about the analysis
            result += f"\n\n--- Video Analysis Metadata ---\n"
            result += f"Video: {Path(video_path).name}\n"
            result += f"Size: {file_size:.1f}MB\n"
            result += f"FPS Sampling: {fps}\n"
            if start_time or end_time:
                result += f"Clip: {start_time or '00:00'} - {end_time or 'end'}\n"

            return result

        except Exception as e:
            return f"Error analyzing video: {str(e)}"

    def _get_mime_type(self, video_path: str) -> str:
        """Determine MIME type from file extension."""
        ext = Path(video_path).suffix.lower()
        mime_types = {
            '.mp4': 'video/mp4',
            '.mpeg': 'video/mpeg',
            '.mpg': 'video/mpg',
            '.mov': 'video/mov',
            '.avi': 'video/avi',
            '.flv': 'video/x-flv',
            '.webm': 'video/webm',
            '.wmv': 'video/wmv',
            '.3gpp': 'video/3gpp'
        }
        return mime_types.get(ext, 'video/mp4')
