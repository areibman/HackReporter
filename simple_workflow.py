#!/usr/bin/env python3
"""
Simple Video Understanding -> Thread Making Workflow

A streamlined script that:
1. Analyzes videos using Google Gemini API
2. Creates tweet threads using Typefully API
3. No CrewAI complexity - just direct API calls with litellm
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import time
import requests
from google import genai
from litellm import completion


class VideoAnalyzer:
    """Simple video analyzer using Google Gemini API"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        self.client = genai.Client(api_key=self.api_key)
    
    def analyze_video(self, video_path: str, custom_prompt: Optional[str] = None) -> Dict:
        """
        Analyze a video and extract key information for social media content
        
        Args:
            video_path: Path to the video file
            custom_prompt: Optional custom prompt for analysis
            
        Returns:
            Dictionary with analysis results
        """
        try:
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
            print(f"📹 Analyzing video: {Path(video_path).name} ({file_size:.1f}MB)")
            
            # Default analysis prompt optimized for hackathon videos
            prompt = custom_prompt or """
            Analyze this hackathon project video and provide a structured analysis:

            1. **Project Overview**:
               - Project name and tagline
               - What problem it solves
               - Target audience/use case
            
            2. **Technical Details**:
               - Key technologies used
               - Notable technical achievements
               - Architecture highlights
            
            3. **Team Information**:
               - Team members (names if mentioned)
               - Roles and backgrounds (if shown)
            
            4. **Demo Highlights**:
               - Most impressive features demonstrated
               - Key timestamps of important moments
               - Visual elements that stand out
            
            5. **Social Media Content**:
               - Generate a compelling tweet-style summary (under 280 characters)
               - Suggest 3-5 key points for a tweet thread
               - Identify quotable moments or achievements
            
            6. **Impact & Innovation**:
               - Potential real-world impact
               - Novel aspects of the solution
               - Technical challenges overcome
            
            Format your response in clear sections with bullet points for easy reading.
            """
            
            # Upload video file
            print("⬆️  Uploading video to Gemini...")
            video_file = self.client.files.upload(file=video_path)
            
            # Wait for processing
            print("⏳ Processing video...")
            for _ in range(30):  # Max 60 seconds
                time.sleep(2)
                file_info = self.client.files.get(name=video_file.name)
                if file_info.state.name == "ACTIVE":
                    break
                elif file_info.state.name == "FAILED":
                    return {"error": "Video processing failed", "success": False}
                print(".", end="", flush=True)
            else:
                return {"error": "Video processing timeout", "success": False}
            
            print("\n🤖 Generating analysis...")
            
            # Generate analysis
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[file_info, prompt]
            )
            
            analysis = response.text
            
            # Clean up uploaded file
            try:
                self.client.files.delete(name=video_file.name)
            except:
                pass  # Don't fail if cleanup fails
            
            return {
                "success": True,
                "video_path": video_path,
                "video_name": Path(video_path).name,
                "file_size_mb": file_size,
                "analysis": analysis,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analyzing video {Path(video_path).name}: {str(e)}",
                "video_path": video_path
            }


class ThreadCreator:
    """Simple thread creator using Typefully API"""
    
    def __init__(self):
        self.api_key = os.getenv("TYPEFULLY_API_KEY")
        if not self.api_key:
            raise ValueError("TYPEFULLY_API_KEY environment variable is required")
        self.base_url = "https://api.typefully.com/v1"
        self.headers = {
            "X-API-KEY": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_thread_content(self, analyses: List[Dict]) -> str:
        """
        Create engaging thread content from video analyses using litellm
        
        Args:
            analyses: List of video analysis results
            
        Returns:
            Thread content as a string
        """
        try:
            # Prepare context for litellm
            context = "Video Analysis Results:\n\n"
            for i, analysis in enumerate(analyses, 1):
                if analysis.get("success"):
                    context += f"Video {i}: {analysis['video_name']}\n"
                    context += f"{analysis['analysis']}\n\n"
                    context += "-" * 50 + "\n\n"
            
            prompt = f"""
            Based on the following hackathon video analyses, create an engaging Twitter thread that:
            
            1. Starts with a compelling hook about the hackathon/event
            2. Highlights the most innovative projects (3-5 projects max)
            3. Focuses on technical achievements and real-world impact
            4. Uses engaging language that would appeal to developers and tech enthusiasts
            5. Includes relevant hashtags and mentions where appropriate
            6. Ends with a call to action or inspiring message
            
            Format as a Twitter thread with numbered tweets (1/n format).
            Keep each tweet under 280 characters.
            Make it shareable and engaging.
            
            Context:
            {context}
            """
            
            print("🧵 Generating thread content with litellm...")
            
            response = completion(
                model="gpt-4",  # or any other model you prefer
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            thread_content = response.choices[0].message.content
            return thread_content
            
        except Exception as e:
            print(f"❌ Error creating thread content: {str(e)}")
            # Fallback to simple summary
            return self._create_simple_summary(analyses)
    
    def _create_simple_summary(self, analyses: List[Dict]) -> str:
        """Fallback method to create simple summary without AI"""
        successful_analyses = [a for a in analyses if a.get("success")]
        
        thread = f"🚀 Analyzed {len(successful_analyses)} hackathon projects! Here are the highlights:\n\n"
        
        for i, analysis in enumerate(successful_analyses[:5], 1):
            video_name = analysis['video_name']
            thread += f"{i}/ {video_name}\n"
            # Extract first few lines of analysis as summary
            lines = analysis['analysis'].split('\n')[:3]
            summary = ' '.join(lines).strip()[:200]
            thread += f"{summary}...\n\n"
        
        thread += f"Amazing to see such innovation! 🎯 #hackathon #innovation #tech"
        return thread
    
    def create_draft(self, content: str, schedule: bool = False) -> Dict:
        """
        Create a draft in Typefully
        
        Args:
            content: Thread content
            schedule: Whether to schedule in next available slot
            
        Returns:
            Dictionary with creation results
        """
        try:
            payload = {
                "content": content,
                "threadify": True,
                "share": True
            }
            
            if schedule:
                payload["schedule-date"] = "next-free-slot"
            
            print("📝 Creating Typefully draft...")
            
            response = requests.post(
                f"{self.base_url}/drafts/",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            result = {
                "success": True,
                "draft_id": data.get("id"),
                "share_url": data.get("share_url"),
                "scheduled_at": data.get("scheduled_at"),
                "status": "scheduled" if schedule else "draft",
                "message": "Draft created successfully!"
            }
            
            print(f"✅ Draft created! ID: {result['draft_id']}")
            if result['share_url']:
                print(f"🔗 Share: {result['share_url']}")
            if result['scheduled_at']:
                print(f"📅 Scheduled: {result['scheduled_at']}")
                
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create draft: {str(e)}"
            }


class SimpleWorkflow:
    """Main workflow orchestrator"""
    
    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.thread_creator = ThreadCreator()
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    async def process_videos(self, directory: str, schedule_thread: bool = False) -> Dict:
        """
        Process all videos in a directory and create a thread
        
        Args:
            directory: Directory containing video files
            schedule_thread: Whether to schedule the thread automatically
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Find video files
            video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
            video_dir = Path(directory)
            video_files = []
            
            for ext in video_extensions:
                video_files.extend(video_dir.glob(f'*{ext}'))
                video_files.extend(video_dir.glob(f'*{ext.upper()}'))
            
            if not video_files:
                return {"error": f"No video files found in {directory}", "success": False}
            
            print(f"🎬 Found {len(video_files)} videos to process")
            
            # Analyze videos sequentially (to avoid API rate limits)
            analyses = []
            for i, video_file in enumerate(video_files, 1):
                print(f"\n--- Processing video {i}/{len(video_files)} ---")
                
                analysis = self.video_analyzer.analyze_video(str(video_file.resolve()))
                analyses.append(analysis)
                
                # Save individual analysis
                if analysis.get("success"):
                    output_file = self.output_dir / f"analysis_{i}_{video_file.stem}.json"
                    with open(output_file, 'w') as f:
                        json.dump(analysis, f, indent=2)
                    print(f"💾 Saved analysis to {output_file}")
                
                # Small delay to be nice to APIs
                if i < len(video_files):
                    await asyncio.sleep(2)
            
            # Save all analyses
            all_analyses_file = self.output_dir / "all_analyses.json"
            with open(all_analyses_file, 'w') as f:
                json.dump(analyses, f, indent=2)
            
            # Create thread content
            print(f"\n🧵 Creating thread from {len(analyses)} analyses...")
            successful_analyses = [a for a in analyses if a.get("success")]
            
            if not successful_analyses:
                return {
                    "success": False,
                    "error": "No videos were successfully analyzed",
                    "analyses": analyses
                }
            
            thread_content = self.thread_creator.create_thread_content(successful_analyses)
            
            # Save thread content
            thread_file = self.output_dir / "thread_content.txt"
            with open(thread_file, 'w') as f:
                f.write(thread_content)
            print(f"💾 Thread content saved to {thread_file}")
            
            # Create Typefully draft
            draft_result = self.thread_creator.create_draft(thread_content, schedule=schedule_thread)
            
            return {
                "success": True,
                "processed_videos": len(video_files),
                "successful_analyses": len(successful_analyses),
                "failed_analyses": len(analyses) - len(successful_analyses),
                "thread_content": thread_content,
                "draft_result": draft_result,
                "output_files": {
                    "analyses": str(all_analyses_file),
                    "thread": str(thread_file)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow error: {str(e)}"
            }


async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_workflow.py <video_directory> [--schedule]")
        print("Example: python simple_workflow.py ./videos --schedule")
        sys.exit(1)
    
    video_dir = sys.argv[1]
    schedule = "--schedule" in sys.argv
    
    print("🚀 Starting Simple Video -> Thread Workflow")
    print(f"📁 Video directory: {video_dir}")
    print(f"📅 Schedule thread: {schedule}")
    print("-" * 50)
    
    workflow = SimpleWorkflow()
    result = await workflow.process_videos(video_dir, schedule_thread=schedule)
    
    if result.get("success"):
        print("\n🎉 Workflow completed successfully!")
        print(f"✅ Processed {result['processed_videos']} videos")
        print(f"✅ {result['successful_analyses']} successful analyses")
        if result['failed_analyses'] > 0:
            print(f"⚠️  {result['failed_analyses']} failed analyses")
        
        print(f"\n📁 Output files:")
        for key, path in result['output_files'].items():
            print(f"  {key}: {path}")
        
        if result['draft_result'].get('success'):
            print(f"\n🔗 Typefully draft: {result['draft_result'].get('share_url', 'Created successfully')}")
    else:
        print(f"\n❌ Workflow failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())