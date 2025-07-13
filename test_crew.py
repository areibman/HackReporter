#!/usr/bin/env python
"""
Test script for HackReporter CrewAI implementation
"""
from hackreporter import HackReporterCrew
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))


def test_crew_initialization():
    """Test that the crew can be initialized"""
    print("Testing crew initialization...")
    try:
        crew = HackReporterCrew()
        print("✅ Crew initialized successfully!")

        # Test agent creation
        print("\nTesting agent creation...")
        agents = [
            crew.video_summarizer(),
            crew.video_captioner(),
            crew.video_noise_remover(),
            crew.video_ranker(),
            crew.person_finder()
        ]
        print(f"✅ Created {len(agents)} agents successfully!")

        # Test task creation
        print("\nTesting task creation...")
        tasks = [
            crew.video_analysis_task(),
            crew.caption_generation_task(),
            crew.audio_enhancement_task(),
            crew.video_ranking_task(),
            crew.person_research_task(),
            crew.final_tweet_composition_task()
        ]
        print(f"✅ Created {len(tasks)} tasks successfully!")

        # Test crew assembly
        print("\nTesting crew assembly...")
        assembled_crew = crew.crew()
        print("✅ Crew assembled successfully!")

        print("\n🎉 All tests passed! The CrewAI setup is working correctly.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nPlease make sure you have:")
        print("1. Installed all dependencies (pip install -r requirements.txt)")
        print("2. Set up your environment variables in .env file")
        return False

    return True


if __name__ == "__main__":
    print("HackReporter CrewAI Test Script")
    print("=" * 50)
    test_crew_initialization()
