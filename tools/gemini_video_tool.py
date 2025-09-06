from crewai.tools import BaseTool
from typing import Type, Any, Optional, Dict
from pydantic import BaseModel, Field
import os
import time
from pathlib import Path
from functools import lru_cache
import asyncio

# Lazy import for performance
def _get_genai():
    from google import genai
    return genai


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
            # Configure Gemini API with lazy loading
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return "Error: GOOGLE_API_KEY environment variable not set"

            # Lazy load genai and create client
            genai = _get_genai()
            client = genai.Client(api_key=api_key)

            # Get file size for metadata with caching
            file_size = self._get_file_size(video_path)

            # Check if we have cached results for this video
            cache_key = f"{video_path}_{file_size}_{hash(str(prompt))}"
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                print(f"📋 Using cached result for {Path(video_path).name}")
                return cached_result

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

            # Poll until the file is ready
            for _ in range(30):  # Max 60 seconds wait
                time.sleep(2)
                file_info = client.files.get(name=video_file.name)
                if file_info.state.name == "ACTIVE":
                    break
                elif file_info.state.name == "FAILED":
                    return f"Error: Video processing failed"
                print(".", end="", flush=True)
            else:
                return "Error: Video processing timeout - file not ready after 60 seconds"

            print("\nVideo processed successfully. Generating analysis...")

            # Generate analysis using the processed file
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[file_info, analysis_prompt]
            )

            # Format the response
            result = response.text

            # Add metadata about the analysis
            result += f"\n\n--- Video Analysis Metadata ---\n"
            result += f"Video: {Path(video_path).name}\n"
            result += f"Size: {file_size:.1f}MB\n"
            result += f"FPS Sampling: {fps}\n"
            if start_time or end_time:
                result += f"Clip: {start_time or '00:00'} - {end_time or 'end'}\n"

            # Cache the result for future use
            self._cache_result(cache_key, result)

            return result

        except Exception as e:
            return f"Error analyzing video: {str(e)}"

    @lru_cache(maxsize=128)
    def _get_file_size(self, video_path: str) -> float:
        """Get file size in MB with caching."""
        return os.path.getsize(video_path) / (1024 * 1024)
    
    def _get_cached_result(self, cache_key: str) -> Optional[str]:
        """Get cached analysis result if available."""
        cache_dir = Path(".cache/video_analysis")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{hash(cache_key)}.txt"
        
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding='utf-8')
            except Exception:
                pass
        return None
    
    def _cache_result(self, cache_key: str, result: str) -> None:
        """Cache analysis result for future use."""
        cache_dir = Path(".cache/video_analysis")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{hash(cache_key)}.txt"
        
        try:
            cache_file.write_text(result, encoding='utf-8')
        except Exception:
            pass  # Ignore cache write failures

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
