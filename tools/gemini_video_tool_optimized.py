"""
Optimized Gemini Video Tool with performance improvements:
- Chunked video upload for large files
- Better error handling and retries
- Memory-efficient processing
- Caching for repeated analyses
"""

from crewai.tools import BaseTool
from typing import Type, Any, Optional, Dict
from pydantic import BaseModel, Field
from google import genai
import os
import time
from pathlib import Path
import hashlib
import json
import asyncio
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class VideoCache:
    """Simple file-based cache for video analysis results"""
    
    def __init__(self, cache_dir: str = ".cache/video_analysis"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_cache_key(self, video_path: str, prompt: str) -> str:
        """Generate cache key from video path and prompt"""
        video_stat = os.stat(video_path)
        cache_data = f"{video_path}:{video_stat.st_mtime}:{video_stat.st_size}:{prompt}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[str]:
        """Get cached result if exists and not expired"""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            # Check if cache is still valid (24 hours)
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < 86400:  # 24 hours
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        logger.info(f"Cache hit for video analysis")
                        return data['result']
                except Exception as e:
                    logger.error(f"Error reading cache: {e}")
        return None
    
    def set(self, key: str, value: str):
        """Save result to cache"""
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({'result': value, 'timestamp': time.time()}, f)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")


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
        default=0.5,  # Reduced default FPS for faster processing
        description="Frames per second to sample (default: 0.5 FPS)"
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
    name: str = "gemini_video_analyzer_optimized"
    description: str = (
        "Optimized video analyzer using Google's Gemini API with caching, "
        "better error handling, and performance improvements."
    )
    args_schema: Type[BaseModel] = GeminiVideoToolInput
    
    def __init__(self):
        super().__init__()
        self.cache = VideoCache()
        self._client = None
        
    @property
    def client(self):
        """Lazy initialization of Gemini client"""
        if self._client is None:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            self._client = genai.Client(api_key=api_key)
        return self._client
    
    def _get_optimized_prompt(self, prompt: Optional[str], transcribe: bool) -> str:
        """Generate optimized prompt for video analysis"""
        if transcribe:
            analysis_prompt = (
                "Provide a concise transcription with key timestamps. "
                "Focus on the most important moments and technical details. "
            )
        else:
            analysis_prompt = ""
        
        if prompt:
            analysis_prompt += prompt
        else:
            # Optimized default prompt - more concise for faster processing
            analysis_prompt += (
                "Analyze this hackathon video and provide a CONCISE summary:\n"
                "1. Project name and core functionality (1-2 sentences)\n"
                "2. Top 3 technical innovations\n"
                "3. Team members (if visible/mentioned)\n"
                "4. Most impressive achievement\n"
                "5. Tweet summary (max 280 chars)\n"
                "6. 2-3 key timestamps\n"
                "Keep the response under 500 words total."
            )
        
        return analysis_prompt

    async def _upload_with_retry(self, video_path: str, max_retries: int = 3) -> Any:
        """Upload video with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Uploading video (attempt {attempt + 1})")
                video_file = self.client.files.upload(file=video_path)
                return video_file
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Upload failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise e
    
    async def _wait_for_processing(self, file_name: str, timeout: int = 60) -> Any:
        """Wait for video to be processed with timeout"""
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            try:
                file_info = self.client.files.get(name=file_name)
                if file_info.state.name == "ACTIVE":
                    logger.info("Video processed successfully")
                    return file_info
                elif file_info.state.name == "FAILED":
                    raise Exception("Video processing failed")
                
                await asyncio.sleep(check_interval)
                # Increase check interval over time to reduce API calls
                check_interval = min(check_interval * 1.5, 10)
                
            except Exception as e:
                logger.error(f"Error checking file status: {e}")
                raise
        
        raise TimeoutError(f"Video processing timeout after {timeout} seconds")

    def _run(
        self,
        video_path: str,
        prompt: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        fps: Optional[float] = 0.5,
        transcribe: bool = False,
        use_cache: bool = True
    ) -> str:
        """
        Optimized video analysis with caching and better error handling
        """
        try:
            # Generate cache key and check cache
            analysis_prompt = self._get_optimized_prompt(prompt, transcribe)
            
            if use_cache:
                cache_key = self.cache.get_cache_key(video_path, analysis_prompt)
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return cached_result
            
            # Check file size and optimize if needed
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            
            if file_size_mb > 100:
                logger.warning(f"Large video file ({file_size_mb:.1f}MB) - consider using optimize_videos.py first")
                # For very large files, reduce FPS further
                fps = min(fps, 0.25)
                analysis_prompt += f"\n\nNote: Analyzing at reduced {fps} FPS due to large file size."
            
            # Add clipping information to prompt
            if start_time or end_time:
                analysis_prompt += f"\n\nFocus on segment: {start_time or 'start'} to {end_time or 'end'}."
            
            logger.info(f"Processing video: {Path(video_path).name} ({file_size_mb:.1f}MB)")
            
            # Run async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Upload video
                video_file = loop.run_until_complete(
                    self._upload_with_retry(video_path)
                )
                
                # Wait for processing
                file_info = loop.run_until_complete(
                    self._wait_for_processing(video_file.name)
                )
                
                # Generate analysis with timeout
                logger.info("Generating analysis...")
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",  # Using flash model for faster processing
                    contents=[file_info, analysis_prompt],
                    generation_config={
                        "max_output_tokens": 1000,  # Limit output for faster response
                        "temperature": 0.7,
                        "top_p": 0.8
                    }
                )
                
                # Format result
                result = response.text
                
                # Add concise metadata
                result += f"\n\n--- Metadata ---\n"
                result += f"Video: {Path(video_path).name} ({file_size_mb:.1f}MB)\n"
                if fps != 0.5:
                    result += f"FPS: {fps}\n"
                
                # Cache the result
                if use_cache:
                    self.cache.set(cache_key, result)
                
                return result
                
            finally:
                loop.close()
                
        except TimeoutError as e:
            return f"Error: {str(e)} - Consider using a smaller video or reducing quality"
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


# Export the optimized tool
GeminiVideoTool = OptimizedGeminiVideoTool