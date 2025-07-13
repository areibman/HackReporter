#!/usr/bin/env python
"""
Test script to verify the aggregation crew uses actual summaries
"""
from crew import HackReporterCrew
from pathlib import Path
import json


def test_aggregation_with_single_summary():
    """Test that the aggregation crew uses the actual Jaiqu summary"""

    # Create the crew instance
    crew_instance = HackReporterCrew()

    # Use the actual summary from the output
    actual_summary = "Jaiqu\nAI-powered natural language to JQ query converter for JSON processing.\nEfficient JSON data extraction tool @JaiquApp"

    # Prepare the aggregation inputs
    output_dir = Path('output')
    aggregation_inputs = {
        'all_summaries': actual_summary,
        'video_count': 1,
        'summaries_file': str(output_dir / 'all_summaries.json')
    }

    print("Testing aggregation with actual Jaiqu summary...")
    print("=" * 60)
    print(f"Input summary:\n{actual_summary}")
    print("=" * 60)

    # Run the aggregator crew
    result = crew_instance.aggregator_crew().kickoff(inputs=aggregation_inputs)

    print("\nResult:")
    print("=" * 60)
    print(result)

    # Check if the output contains the actual project
    output_file = Path("output/tweet_thread.md")
    if output_file.exists():
        content = output_file.read_text()
        print("\nGenerated tweet thread:")
        print("=" * 60)
        print(content)

        # Verify the content
        if "Jaiqu" in content:
            print("\n✅ SUCCESS: Thread contains the actual Jaiqu project!")
        else:
            print("\n❌ FAILURE: Thread does not contain Jaiqu project")

        if "SaveThePlanet" in content or "CodeConnect" in content or "HealthGuard" in content:
            print("❌ FAILURE: Thread contains hallucinated projects!")
        else:
            print("✅ SUCCESS: No hallucinated projects found!")


if __name__ == "__main__":
    test_aggregation_with_single_summary()
