#!/usr/bin/env python3
"""
Simple Video Processor - Video Understanding -> Thread Making Script
Removes all CrewAI complexity and uses litellm for direct API calls
"""

import os
import json
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional
import requests
from google import genai
from litellm import completion


class SimpleVideoProcessor:
    """Simple video processing without CrewAI complexity"""
    
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.typefully_api_key = os.getenv("TYPEFULLY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        if not self.typefully_api_key:
            print("Warning: TYPEFULLY_API_KEY not set - will save threads to file instead")
        if not self.openai_api_key:
            print("Warning: OPENAI_API_KEY not set - will use Google Gemini for text generation")
    
    def analyze_video(self, video_path: str) -> str:
        """Analyze a video using Google Gemini API"""
        try:
            print(f"📹 Analyzing video: {Path(video_path).name}")
            
            # Configure Gemini API
            client = genai.Client(api_key=self.google_api_key)
            
            # Get file size for metadata
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
            print(f"📊 File size: {file_size:.1f}MB")
            
            # Analysis prompt for hackathon videos
            analysis_prompt = """
            Analyze this hackathon project video and provide a comprehensive summary including:
            
            1. Project name and what it does
            2. Key technical innovations and features
            3. Team members (if mentioned or shown)
            4. Most impressive technical achievements
            5. Potential use cases and impact
            6. Key timestamps of important moments
            7. Any technical challenges mentioned
            8. Demo highlights and visual elements
            
            Format the response as a clear, structured summary that could be used to create engaging social media content.
            """
            
            print("🔄 Uploading video to Gemini...")
            
            # Upload the video file
            video_file = client.files.upload(file=video_path)
            
            # Wait for file to be processed
            print("⏳ Waiting for video processing...")
            for _ in range(30):  # Max 60 seconds wait
                time.sleep(2)
                file_info = client.files.get(name=video_file.name)
                if file_info.state.name == "ACTIVE":
                    break
                elif file_info.state.name == "FAILED":
                    return f"Error: Video processing failed for {Path(video_path).name}"
                print(".", end="", flush=True)
            else:
                return f"Error: Video processing timeout for {Path(video_path).name}"
            
            print("\n✅ Video processed successfully. Generating analysis...")
            
            # Generate analysis using the processed file
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[file_info, analysis_prompt]
            )
            
            result = response.text
            
            # Add metadata
            result += f"\n\n--- Video Analysis Metadata ---\n"
            result += f"Video: {Path(video_path).name}\n"
            result += f"Size: {file_size:.1f}MB\n"
            
            print(f"✅ Analysis complete for {Path(video_path).name}")
            return result
            
        except Exception as e:
            error_msg = f"Error analyzing video {Path(video_path).name}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def create_tweet_thread(self, summaries: List[str], video_count: int) -> str:
        """Create a tweet thread from video summaries using litellm"""
        try:
            print(f"🧵 Creating tweet thread from {video_count} video summaries...")
            
            # Combine all summaries
            combined_summaries = "\n\n".join(summaries)
            
            # Create thread prompt
            thread_prompt = f"""
            You are a social media expert creating an engaging tweet thread about hackathon projects.
            
            Here are summaries from {video_count} hackathon project videos:
            
            {combined_summaries}
            
            Create an engaging tweet thread that:
            1. Starts with a compelling hook about the hackathon
            2. Highlights the most impressive projects and innovations
            3. Includes specific technical achievements and use cases
            4. Ends with a call to action or reflection on the hackathon spirit
            5. Uses appropriate hashtags and mentions
            6. Each tweet should be under 280 characters
            7. Format as a numbered thread (1/5, 2/5, etc.)
            
            Make it engaging, technical but accessible, and highlight the innovation and creativity shown.
            """
            
            # Use litellm to generate the thread
            if self.openai_api_key:
                # Use OpenAI if available
                response = completion(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": thread_prompt}],
                    api_key=self.openai_api_key,
                    max_tokens=2000,
                    temperature=0.7
                )
            else:
                # Fallback to Google Gemini
                client = genai.Client(api_key=self.google_api_key)
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=thread_prompt
                )
                response = type('Response', (), {'choices': [type('Choice', (), {'message': type('Message', (), {'content': response.text})()})()]})()
            
            thread_content = response.choices[0].message.content
            
            print("✅ Tweet thread created successfully!")
            return thread_content
            
        except Exception as e:
            error_msg = f"Error creating tweet thread: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def save_to_typefully(self, thread_content: str) -> Dict:
        """Save thread to Typefully or return error info"""
        if not self.typefully_api_key:
            return {
                "success": False,
                "error": "TYPEFULLY_API_KEY not set",
                "content": thread_content
            }
        
        try:
            base_url = "https://api.typefully.com/v1"
            headers = {
                "X-API-KEY": f"Bearer {self.typefully_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "content": thread_content,
                "threadify": True,
                "share": True
            }
            
            response = requests.post(
                f"{base_url}/drafts/",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            result = {
                "success": True,
                "draft_id": data.get("id"),
                "share_url": data.get("share_url"),
                "scheduled_at": data.get("scheduled_at"),
                "message": "Draft created successfully in Typefully"
            }
            
            print(f"✅ Typefully draft created! ID: {result['draft_id']}")
            if result['share_url']:
                print(f"🔗 Shareable link: {result['share_url']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to create Typefully draft: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "content": thread_content
            }
    
    def save_to_file(self, thread_content: str, output_dir: str = "output"):
        """Save thread content to a file"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = int(time.time())
        filename = f"tweet_thread_{timestamp}.md"
        filepath = output_path / filename
        
        with open(filepath, 'w') as f:
            f.write(thread_content)
        
        print(f"💾 Thread saved to: {filepath}")
        return str(filepath)
    
    async def process_videos(self, directory: str, max_concurrent: int = 2) -> Dict:
        """Process all videos in a directory and create a tweet thread"""
        
        # Find video files
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        video_dir = Path(directory)
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(video_dir.glob(f'*{ext}'))
            video_files.extend(video_dir.glob(f'*{ext.upper()}'))
        
        if not video_files:
            return {"error": f"No video files found in {directory}"}
        
        print(f"🎬 Found {len(video_files)} video files to process")
        
        # Process videos with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_video_with_limit(video_file: Path, index: int):
            async with semaphore:
                print(f"🔄 Processing video {index+1}/{len(video_files)}: {video_file.name}")
                try:
                    result = self.analyze_video(str(video_file.resolve()))
                    print(f"✅ Completed video {index+1}")
                    return result
                except Exception as e:
                    error_msg = f"Error processing {video_file.name}: {str(e)}"
                    print(f"❌ {error_msg}")
                    return error_msg
        
        # Create tasks
        tasks = [process_video_with_limit(video_file, i) for i, video_file in enumerate(video_files)]
        
        # Execute all tasks
        print(f"🚀 Processing {len(tasks)} videos with max {max_concurrent} concurrent...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and count successes
        summaries = []
        errors = []
        for i, result in enumerate(results):
            if isinstance(result, Exception) or str(result).startswith("Error"):
                errors.append(f"Video {i+1}: {result}")
            else:
                summaries.append(str(result))
        
        print(f"📊 Processed {len(summaries)}/{len(video_files)} videos successfully")
        if errors:
            print(f"❌ {len(errors)} errors occurred")
            for error in errors:
                print(f"   {error}")
        
        # Create tweet thread
        if summaries:
            thread_content = self.create_tweet_thread(summaries, len(video_files))
            
            # Save to Typefully
            typefully_result = self.save_to_typefully(thread_content)
            
            # Always save to file as backup
            file_path = self.save_to_file(thread_content)
            
            return {
                "processed_videos": len(video_files),
                "successful_analyses": len(summaries),
                "errors": errors,
                "thread_content": thread_content,
                "typefully_result": typefully_result,
                "file_path": file_path
            }
        else:
            return {
                "error": "No videos were successfully processed",
                "errors": errors
            }


async def main():
    """Main function to run the video processor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Video Processor - Video Understanding -> Thread Making")
    parser.add_argument("directory", help="Directory containing video files")
    parser.add_argument("--max-concurrent", type=int, default=2, help="Maximum concurrent video processing (default: 2)")
    parser.add_argument("--sequential", action="store_true", help="Process videos sequentially (useful for API quotas)")
    
    args = parser.parse_args()
    
    # Set sequential mode if requested
    if args.sequential:
        args.max_concurrent = 1
        print("🔄 Running in sequential mode")
    
    try:
        processor = SimpleVideoProcessor()
        result = await processor.process_videos(args.directory, args.max_concurrent)
        
        print("\n" + "="*50)
        print("🎉 PROCESSING COMPLETE")
        print("="*50)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ Successfully processed {result['successful_analyses']}/{result['processed_videos']} videos")
            print(f"📄 Thread saved to: {result['file_path']}")
            
            if result['typefully_result']['success']:
                print(f"🐦 Typefully draft created: {result['typefully_result']['draft_id']}")
                if result['typefully_result']['share_url']:
                    print(f"🔗 Shareable link: {result['typefully_result']['share_url']}")
            else:
                print(f"⚠️  Typefully error: {result['typefully_result']['error']}")
        
        # Print thread preview
        if "thread_content" in result:
            print("\n" + "="*50)
            print("🧵 TWEET THREAD PREVIEW")
            print("="*50)
            print(result['thread_content'][:1000] + "..." if len(result['thread_content']) > 1000 else result['thread_content'])
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)