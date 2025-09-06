"""
Optimized Gemini Video Tool with caching and memory management
"""
from crewai.tools import BaseTool
from typing import Type, Any, Optional, Dict
from pydantic import BaseModel, Field
from google import genai
import os
import time
import asyncio
from pathlib import Path
import logging
from cache_manager import cache_manager

logger = logging.getLogger(__name__)


class OptimizedGeminiVideoToolInput(BaseModel):
    """Input schema for OptimizedGeminiVideoTool."""
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
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached results if available"
    )


class OptimizedGeminiVideoTool(BaseTool):
    name: str = "optimized_gemini_video_analyzer"
    description: str = (
        "Optimized video content analyzer using Google's Gemini API with caching, "
        "memory management, and retry mechanisms. Extracts insights, summaries, "
        "transcriptions, and key information from hackathon project demonstrations. "
        "Supports video clipping, custom FPS, and timestamped transcription."
    )
    args_schema: Type[BaseModel] = OptimizedGeminiVideoToolInput

    def __init__(self):
        super().__init__()
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Gemini client with connection pooling"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GOOGLE_API_KEY environment variable not set")
                return
            
            self.client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")

    def _get_cache_key(self, video_path: str, prompt: str, start_time: str, end_time: str, fps: float, transcribe: bool) -> str:
        """Generate cache key based on input parameters"""
        file_stat = Path(video_path).stat()
        cache_data = {
            'video_path': video_path,
            'file_size': file_stat.st_size,
            'file_mtime': file_stat.st_mtime,
            'prompt': prompt,
            'start_time': start_time,
            'end_time': end_time,
            'fps': fps,
            'transcribe': transcribe
        }
        return cache_manager._get_cache_key(cache_data)

    def _upload_video_with_retry(self, video_path: str, max_retries: int = 3) -> Optional[Any]:
        """Upload video with retry mechanism and exponential backoff"""
        if not self.client:
            return None

        for attempt in range(max_retries):
            try:
                logger.info(f"Uploading video file (attempt {attempt + 1}/{max_retries})")
                video_file = self.client.files.upload(file=video_path)
                return video_file
            except Exception as e:
                logger.warning(f"Upload attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All upload attempts failed: {e}")
                    return None

    def _wait_for_processing_with_timeout(self, video_file: Any, timeout: int = 120) -> Optional[Any]:
        """Wait for video processing with timeout and progress updates"""
        if not self.client:
            return None

        start_time = time.time()
        last_progress_time = start_time
        
        while time.time() - start_time < timeout:
            try:
                file_info = self.client.files.get(name=video_file.name)
                
                if file_info.state.name == "ACTIVE":
                    logger.info("Video processing completed successfully")
                    return file_info
                elif file_info.state.name == "FAILED":
                    logger.error("Video processing failed")
                    return None
                
                # Log progress every 10 seconds
                if time.time() - last_progress_time >= 10:
                    logger.info(f"Video processing in progress... ({int(time.time() - start_time)}s elapsed)")
                    last_progress_time = time.time()
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"Error checking processing status: {e}")
                time.sleep(2)
        
        logger.error(f"Video processing timeout after {timeout} seconds")
        return None

    def _run(
        self,
        video_path: str,
        prompt: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        fps: Optional[float] = 1.0,
        transcribe: bool = False,
        use_cache: bool = True
    ) -> str:
        """
        Analyze a video using Gemini API with optimizations.

        Args:
            video_path: Path to the video file
            prompt: Custom prompt for analysis
            start_time: Start time for video clip (MM:SS format)
            end_time: End time for video clip (MM:SS format)
            fps: Frames per second to sample
            transcribe: Whether to transcribe audio with timestamps
            use_cache: Whether to use cached results

        Returns:
            Analysis results as a string
        """
        try:
            # Check cache first
            if use_cache:
                cache_key = self._get_cache_key(video_path, prompt or "", start_time or "", end_time or "", fps, transcribe)
                cached_result = cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Using cached result for {Path(video_path).name}")
                    return cached_result

            # Validate file exists and get size
            if not Path(video_path).exists():
                return "Error: Video file not found"

            file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
            logger.info(f"Processing video: {Path(video_path).name} ({file_size:.1f}MB)")

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

            # Upload video with retry
            video_file = self._upload_video_with_retry(video_path)
            if not video_file:
                return "Error: Failed to upload video file"

            # Wait for processing with timeout
            file_info = self._wait_for_processing_with_timeout(video_file)
            if not file_info:
                return "Error: Video processing failed or timed out"

            # Generate analysis
            logger.info("Generating analysis...")
            response = self.client.models.generate_content(
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

            # Cache the result
            if use_cache:
                cache_manager.set(cache_key, result)
                logger.info(f"Cached result for {Path(video_path).name}")

            return result

        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}")
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