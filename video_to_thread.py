#!/usr/bin/env python3
"""
Simple video understanding to Twitter thread generation script.
No CrewAI, just straightforward litellm calls.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import argparse
from datetime import datetime

import litellm
from google import genai
import requests


class VideoAnalyzer:
    """Simple video analyzer using Google Gemini directly."""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = genai.Client(api_key=self.api_key)
    
    async def analyze_video(self, video_path: str) -> Dict:
        """
        Analyze a single video and extract key information.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video analysis results
        """
        try:
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
            print(f"📹 Analyzing video: {Path(video_path).name} ({file_size:.1f}MB)")
            
            # Upload video to Gemini
            print("  Uploading video...")
            video_file = self.client.files.upload(file=video_path)
            
            # Wait for processing
            print("  Processing video...")
            for _ in range(30):
                await asyncio.sleep(2)
                file_info = self.client.files.get(name=video_file.name)
                if file_info.state.name == "ACTIVE":
                    break
                elif file_info.state.name == "FAILED":
                    raise Exception("Video processing failed")
            else:
                raise Exception("Video processing timeout")
            
            # Analyze the video
            print("  Generating analysis...")
            prompt = """
            Analyze this hackathon project video and provide a structured response with:
            
            1. **Project Name**: The name of the project
            2. **What It Does**: Clear explanation of the project's purpose and functionality
            3. **Key Features**: List the main features demonstrated (bullet points)
            4. **Technical Stack**: Technologies and tools used
            5. **Team Members**: Names of team members if mentioned/shown
            6. **Demo Highlights**: Most impressive moments from the demo
            7. **Use Cases**: Potential applications and impact
            8. **Tweet Summary**: A compelling 280-character summary perfect for Twitter
            9. **Memorable Quote**: Any standout quote from the presentation
            10. **Innovation Score**: Rate the innovation level (1-10) with brief justification
            
            Be specific and extract actual details from the video, not generic descriptions.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[file_info, prompt]
            )
            
            return {
                "video_name": Path(video_path).name,
                "file_size_mb": file_size,
                "analysis": response.text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ❌ Error analyzing video: {str(e)}")
            return {
                "video_name": Path(video_path).name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class ThreadComposer:
    """Simple thread composer using litellm."""
    
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        # Set up litellm with API keys from environment
        litellm.set_verbose = False
    
    async def create_thread(self, video_analyses: List[Dict]) -> str:
        """
        Create a Twitter thread from video analyses.
        
        Args:
            video_analyses: List of video analysis results
            
        Returns:
            Formatted Twitter thread as string
        """
        print("\n🧵 Creating Twitter thread from analyses...")
        
        # Filter out errors
        successful_analyses = [
            a for a in video_analyses 
            if "error" not in a and "analysis" in a
        ]
        
        if not successful_analyses:
            return "No successful video analyses to create thread from."
        
        # Combine all analyses
        combined_analyses = "\n\n---\n\n".join([
            f"Video: {a['video_name']}\n{a['analysis']}"
            for a in successful_analyses
        ])
        
        # Create the thread using litellm
        prompt = f"""
        Based on these hackathon project video analyses, create an engaging Twitter thread.
        
        VIDEO ANALYSES:
        {combined_analyses}
        
        REQUIREMENTS:
        1. Start with a hook tweet that captures attention
        2. Highlight the most innovative and impressive projects
        3. Use emojis appropriately to increase engagement
        4. Include specific technical details that developers will appreciate
        5. Keep each tweet under 280 characters
        6. Number the tweets (1/n, 2/n, etc.)
        7. End with a call-to-action or thought-provoking question
        8. Aim for 5-10 tweets total
        
        FORMAT:
        Return ONLY the tweet thread, with each tweet on a new line.
        Do not include any other text or explanations.
        """
        
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a tech-savvy social media expert who creates viral Twitter threads about hackathon projects."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Error creating thread: {str(e)}")
            return f"Error creating thread: {str(e)}"


class TypefullyPublisher:
    """Simple Typefully integration for publishing drafts."""
    
    def __init__(self):
        self.api_key = os.getenv("TYPEFULLY_API_KEY")
        self.base_url = "https://api.typefully.com/v1"
    
    def create_draft(self, content: str, schedule: bool = False) -> Dict:
        """
        Create a draft in Typefully.
        
        Args:
            content: The thread content
            schedule: Whether to schedule for next available slot
            
        Returns:
            API response dictionary
        """
        if not self.api_key:
            print("⚠️  TYPEFULLY_API_KEY not set, skipping draft creation")
            return {"success": False, "error": "No API key"}
        
        headers = {
            "X-API-KEY": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": content,
            "threadify": True,
            "share": True
        }
        
        if schedule:
            payload["schedule-date"] = "next-free-slot"
        
        try:
            response = requests.post(
                f"{self.base_url}/drafts/",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Typefully draft created! ID: {data.get('id')}")
            if data.get('share_url'):
                print(f"🔗 Share URL: {data.get('share_url')}")
            
            return data
            
        except Exception as e:
            print(f"❌ Failed to create Typefully draft: {str(e)}")
            return {"success": False, "error": str(e)}


async def process_videos(directory: str, model: str = "gpt-4o", typefully: bool = False):
    """
    Main function to process videos and generate Twitter thread.
    
    Args:
        directory: Path to directory containing videos
        model: LLM model to use for thread composition
        typefully: Whether to create a Typefully draft
    """
    # Find video files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    video_dir = Path(directory)
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f'*{ext}'))
        video_files.extend(video_dir.glob(f'*{ext.upper()}'))
    
    if not video_files:
        print(f"❌ No video files found in {directory}")
        return
    
    print(f"Found {len(video_files)} video(s) to process\n")
    
    # Initialize components
    analyzer = VideoAnalyzer()
    composer = ThreadComposer(model=model)
    
    # Analyze videos (with concurrency limit to avoid API quotas)
    MAX_CONCURRENT = 2
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def analyze_with_limit(video_path):
        async with semaphore:
            return await analyzer.analyze_video(str(video_path))
    
    # Process all videos
    print("🎬 Starting video analysis...\n")
    tasks = [analyze_with_limit(vf) for vf in video_files]
    analyses = await asyncio.gather(*tasks)
    
    # Save analyses
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / 'video_analyses.json', 'w') as f:
        json.dump(analyses, f, indent=2)
    print(f"\n💾 Saved analyses to output/video_analyses.json")
    
    # Create thread
    thread = await composer.create_thread(analyses)
    
    # Save thread
    with open(output_dir / 'twitter_thread.txt', 'w') as f:
        f.write(thread)
    print(f"💾 Saved thread to output/twitter_thread.txt")
    
    # Display thread
    print("\n" + "="*50)
    print("📱 GENERATED TWITTER THREAD:")
    print("="*50)
    print(thread)
    print("="*50)
    
    # Optionally publish to Typefully
    if typefully:
        publisher = TypefullyPublisher()
        publisher.create_draft(thread, schedule=False)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert hackathon videos to Twitter threads"
    )
    parser.add_argument(
        "directory",
        help="Directory containing video files"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model to use (default: gpt-4o)"
    )
    parser.add_argument(
        "--typefully",
        action="store_true",
        help="Create a draft in Typefully"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the async process
    asyncio.run(process_videos(
        args.directory,
        model=args.model,
        typefully=args.typefully
    ))


if __name__ == "__main__":
    main()