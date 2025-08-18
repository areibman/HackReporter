#!/usr/bin/env python3
"""
Test script for the simple workflow
"""

import os
import json
from pathlib import Path
from simple_workflow import VideoAnalyzer, ThreadCreator, SimpleWorkflow


def test_video_analyzer():
    """Test video analyzer (requires GOOGLE_API_KEY)"""
    print("🧪 Testing VideoAnalyzer...")
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Skipping VideoAnalyzer test - GOOGLE_API_KEY not set")
        return
    
    try:
        analyzer = VideoAnalyzer()
        print("✅ VideoAnalyzer initialized successfully")
    except Exception as e:
        print(f"❌ VideoAnalyzer initialization failed: {e}")


def test_thread_creator():
    """Test thread creator (requires TYPEFULLY_API_KEY)"""
    print("\n🧪 Testing ThreadCreator...")
    
    if not os.getenv("TYPEFULLY_API_KEY"):
        print("⚠️  Skipping ThreadCreator test - TYPEFULLY_API_KEY not set")
        return
    
    try:
        creator = ThreadCreator()
        print("✅ ThreadCreator initialized successfully")
        
        # Test thread content creation with mock data
        mock_analyses = [
            {
                "success": True,
                "video_name": "test_project.mp4",
                "analysis": "Project: AI Code Assistant\n\nThis project creates an AI-powered code assistant that helps developers write better code faster. The team used Python, OpenAI API, and React for the frontend.\n\nKey features:\n- Real-time code suggestions\n- Bug detection\n- Code optimization\n\nThe demo showed impressive results with 40% faster coding speed."
            }
        ]
        
        # Test without litellm first (fallback method)
        content = creator._create_simple_summary(mock_analyses)
        print("✅ Simple summary generation works")
        print(f"Sample content: {content[:100]}...")
        
    except Exception as e:
        print(f"❌ ThreadCreator test failed: {e}")


def test_environment():
    """Test environment setup"""
    print("🧪 Testing Environment Setup...")
    
    required_vars = ["GOOGLE_API_KEY", "TYPEFULLY_API_KEY"]
    optional_vars = ["OPENAI_API_KEY"]
    
    missing_required = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is missing")
            missing_required.append(var)
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var} is set (optional)")
        else:
            print(f"⚠️  {var} is not set (optional)")
    
    if missing_required:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing_required)}")
        print("Please set these in your .env file")
    else:
        print("\n✅ All required environment variables are set!")


def test_output_directory():
    """Test output directory creation"""
    print("\n🧪 Testing Output Directory...")
    
    output_dir = Path("output")
    if output_dir.exists():
        print(f"✅ Output directory exists: {output_dir}")
    else:
        try:
            output_dir.mkdir(exist_ok=True)
            print(f"✅ Created output directory: {output_dir}")
        except Exception as e:
            print(f"❌ Failed to create output directory: {e}")


def test_dependencies():
    """Test that all required packages are installed"""
    print("\n🧪 Testing Dependencies...")
    
    required_packages = [
        ("google.genai", "google-genai"),
        ("litellm", "litellm"),
        ("requests", "requests"),
    ]
    
    for package_name, pip_name in required_packages:
        try:
            __import__(package_name)
            print(f"✅ {pip_name} is installed")
        except ImportError:
            print(f"❌ {pip_name} is not installed - run: pip install {pip_name}")


def create_test_video_info():
    """Create a sample video info file for testing"""
    print("\n🧪 Creating test data...")
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    test_data = {
        "test_analyses": [
            {
                "success": True,
                "video_name": "ai_assistant_demo.mp4",
                "file_size_mb": 25.3,
                "analysis": """
Project Overview:
- Project name: CodeMate AI
- Problem: Developers spend too much time on repetitive coding tasks
- Target audience: Software developers and coding students

Technical Details:
- Technologies: Python, OpenAI GPT-4, React, FastAPI
- Architecture: Microservices with REST API
- Notable achievement: 95% accuracy in code suggestions

Team Information:
- Sarah Chen (ML Engineer)
- Mike Rodriguez (Full-stack Developer)
- Alex Kim (UI/UX Designer)

Demo Highlights:
- Real-time code completion (timestamp: 2:30)
- Bug detection feature (timestamp: 4:15)
- Performance optimization suggestions (timestamp: 6:45)

Social Media Content:
Tweet summary: "CodeMate AI: The game-changing assistant that makes developers 40% more productive with AI-powered code suggestions, bug detection, and optimization tips! 🚀 #hackathon #AI #coding"

Key thread points:
- Revolutionary AI code assistant
- 40% productivity boost proven
- Real-time suggestions and bug detection
- Built by talented team in 48 hours
- Open source and ready to use
                """,
                "timestamp": 1704067200
            }
        ]
    }
    
    test_file = output_dir / "test_analyses.json"
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"✅ Created test data file: {test_file}")
    return test_file


def main():
    """Run all tests"""
    print("🚀 Testing Simple Video Workflow")
    print("=" * 50)
    
    test_environment()
    test_dependencies()
    test_output_directory()
    test_video_analyzer()
    test_thread_creator()
    create_test_video_info()
    
    print("\n" + "=" * 50)
    print("🎉 Test suite completed!")
    print("\nNext steps:")
    print("1. Set up your .env file with API keys")
    print("2. Test with actual videos: python simple_workflow.py /path/to/videos")
    print("3. Check the output/ directory for results")


if __name__ == "__main__":
    main()