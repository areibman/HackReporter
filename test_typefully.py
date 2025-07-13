#!/usr/bin/env python3
"""Test script for Typefully integration"""

import os
from dotenv import load_dotenv
from tools.typefully_tool import TypefullyTool

# Load environment variables
load_dotenv()


def test_typefully_draft():
    """Test creating a draft in Typefully"""

    # Sample tweet thread content
    test_thread = """🚀 Test Thread from HackReporter

1/ This is a test thread to verify our Typefully integration is working correctly.

2/ HackReporter can now automatically create drafts in Typefully after processing hackathon videos.

3/ Features:
- Auto-split long content
- Shareable preview links  
- Ready to schedule or publish

4/ This makes it super easy to review and edit threads before posting! 🎉"""

    # Initialize the tool
    tool = TypefullyTool()

    # Create a draft
    print("Creating Typefully draft...")
    result = tool._run(
        content=test_thread,
        auto_split=True,
        share=True
    )

    # Display results
    if result['success']:
        print("\n✅ Success!")
        print(f"Draft ID: {result['draft_id']}")
        if result['share_url']:
            print(f"Share URL: {result['share_url']}")
        print(f"Status: {result['status']}")
    else:
        print(f"\n❌ Error: {result['error']}")

    return result


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("TYPEFULLY_API_KEY"):
        print("⚠️  TYPEFULLY_API_KEY not found in environment variables!")
        print("Please add it to your .env file")
        exit(1)

    # Run the test
    test_typefully_draft()
