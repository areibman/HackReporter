#!/usr/bin/env python3
"""
Test script to verify the simplified video processor setup
"""

import os
import sys

def test_imports():
    """Test that all required imports work"""
    print("🔍 Testing imports...")
    
    try:
        import asyncio
        print("✅ asyncio")
    except ImportError as e:
        print(f"❌ asyncio: {e}")
        return False
    
    try:
        import requests
        print("✅ requests")
    except ImportError as e:
        print(f"❌ requests: {e}")
        return False
    
    try:
        from google import genai
        print("✅ google-genai")
    except ImportError as e:
        print(f"❌ google-genai: {e}")
        return False
    
    try:
        from litellm import completion
        print("✅ litellm")
    except ImportError as e:
        print(f"❌ litellm: {e}")
        return False
    
    try:
        from pathlib import Path
        print("✅ pathlib")
    except ImportError as e:
        print(f"❌ pathlib: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing environment variables...")
    
    google_key = os.getenv("GOOGLE_API_KEY")
    typefully_key = os.getenv("TYPEFULLY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if google_key:
        print("✅ GOOGLE_API_KEY set")
    else:
        print("⚠️  GOOGLE_API_KEY not set (required)")
        return False
    
    if typefully_key:
        print("✅ TYPEFULLY_API_KEY set")
    else:
        print("⚠️  TYPEFULLY_API_KEY not set (optional)")
    
    if openai_key:
        print("✅ OPENAI_API_KEY set")
    else:
        print("⚠️  OPENAI_API_KEY not set (optional, will use Gemini fallback)")
    
    return True

def test_gemini_connection():
    """Test basic Gemini API connection"""
    print("\n🔍 Testing Gemini API connection...")
    
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        print("❌ Cannot test Gemini connection - no API key")
        return False
    
    try:
        from google import genai
        client = genai.Client(api_key=google_key)
        
        # Test with a simple text generation
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say 'Hello, Gemini is working!'"
        )
        
        if "Hello" in response.text or "working" in response.text.lower():
            print("✅ Gemini API connection successful")
            return True
        else:
            print(f"⚠️  Gemini API responded but unexpected content: {response.text[:100]}")
            return True  # Still consider it working
            
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False

def test_litellm():
    """Test litellm functionality"""
    print("\n🔍 Testing litellm...")
    
    try:
        from litellm import completion
        
        # Test with a simple completion
        response = completion(
            model="gpt-3.5-turbo",  # Use a simple model for testing
            messages=[{"role": "user", "content": "Say 'Hello, litellm is working!'"}],
            max_tokens=50
        )
        
        if response and hasattr(response, 'choices'):
            print("✅ litellm working")
            return True
        else:
            print("⚠️  litellm responded but unexpected format")
            return True
            
    except Exception as e:
        print(f"⚠️  litellm test failed (this is okay if no OpenAI key): {e}")
        return True  # Don't fail the test for this

def main():
    """Run all tests"""
    print("🧪 Testing Simple Video Processor Setup")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test environment
    if not test_environment():
        all_passed = False
    
    # Test API connections
    if not test_gemini_connection():
        all_passed = False
    
    # Test litellm (optional)
    test_litellm()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All required tests passed! Your setup is ready.")
        print("\nYou can now run:")
        print("python simple_video_processor.py /path/to/videos")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nMake sure to:")
        print("1. Install dependencies: pip install -r requirements_simple.txt")
        print("2. Set GOOGLE_API_KEY environment variable")
        print("3. Optionally set TYPEFULLY_API_KEY and OPENAI_API_KEY")
        sys.exit(1)

if __name__ == "__main__":
    main()