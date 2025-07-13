# Enhanced Video Understanding Features

## Overview

The HackReporter now uses Gemini's advanced video understanding API, providing powerful capabilities for analyzing hackathon project videos.

## Key Features

### 1. Automatic File Size Handling
- **Small videos (<20MB)**: Processed inline for faster analysis
- **Large videos (>20MB)**: Automatically uploaded using File API
- No manual configuration needed - the tool handles this automatically

### 2. Audio Transcription
Enable transcription to get:
- Full audio transcript with timestamps
- Speaker identification (when clear)
- Technical term recognition
- Synchronized with visual events

Example:
```python
video_tool._run(
    video_path="demo.mp4",
    transcribe=True
)
```

### 3. Video Clipping
Analyze specific portions of videos:
- Specify start and end times in MM:SS format
- Useful for focusing on demo sections
- Reduces token usage for long videos

Example:
```python
# Analyze only the demo portion (1:30 to 3:45)
video_tool._run(
    video_path="presentation.mp4",
    start_time="01:30",
    end_time="03:45",
    prompt="Analyze the technical demonstration"
)
```

### 4. Custom Frame Rate Sampling
- Default: 1 frame per second (FPS)
- Increase for detailed UI/UX analysis
- Decrease for long videos to save tokens

Example:
```python
# High detail analysis at 5 FPS
video_tool._run(
    video_path="ui_demo.mp4",
    fps=5.0,
    prompt="Describe all UI interactions in detail"
)
```

### 5. Supported Video Formats
- mp4, mpeg, mov, avi, flv, mpg, webm, wmv, 3gpp
- Automatic MIME type detection
- No conversion needed

## Token Usage Optimization

### Token Calculation
- ~300 tokens per second at default settings (1 FPS)
- Higher FPS = more tokens
- Clipping reduces tokens by analyzing only relevant sections

### Best Practices
1. **For pitch videos**: Use transcription, default FPS
2. **For UI demos**: Use higher FPS (3-5), focus on visual
3. **For long videos**: Use clipping to analyze key sections
4. **For interviews**: Enable transcription, low FPS (0.5)

## Advanced Prompting

### Hackathon-Specific Analysis
The default prompt extracts:
1. Project name and description
2. Technical innovations
3. Team members
4. Key features with timestamps
5. Tweet-ready summary
6. Demo highlights
7. Technical challenges
8. Visual elements

### Custom Prompts
```python
# Social media focused
video_tool._run(
    video_path="project.mp4",
    prompt="Create a viral Twitter thread about this project with emojis"
)

# Technical deep-dive
video_tool._run(
    video_path="demo.mp4",
    fps=3.0,
    prompt="Analyze the technical architecture and implementation details"
)

# Investor pitch analysis
video_tool._run(
    video_path="pitch.mp4",
    transcribe=True,
    prompt="Extract problem, solution, market size, and business model"
)
```

## Integration with CrewAI

The Video Summarizer agent automatically uses these features:
- Transcribes audio for quote extraction
- Identifies key timestamps for highlights
- Analyzes visual elements for engagement
- Creates tweet-ready summaries

## Examples

### Example 1: Quick Project Summary
```python
result = video_tool._run(
    video_path="hackathon_demo.mp4"
)
# Uses default settings for balanced analysis
```

### Example 2: Detailed Demo Analysis
```python
result = video_tool._run(
    video_path="live_demo.mp4",
    start_time="02:00",
    end_time="05:00",
    fps=3.0,
    prompt="Focus on user interactions and technical implementation"
)
```

### Example 3: Interview Transcription
```python
result = video_tool._run(
    video_path="team_interview.mp4",
    transcribe=True,
    fps=0.5,  # Low FPS since focus is on audio
    prompt="Extract team quotes about their vision and challenges"
)
```

## Tips for Best Results

1. **Pre-process videos**: Ensure good audio quality for transcription
2. **Strategic clipping**: Identify key sections before processing
3. **Prompt engineering**: Be specific about what you want to extract
4. **Batch processing**: Use different strategies for different video types
5. **Token management**: Monitor usage and adjust FPS/clipping accordingly

## Error Handling

The tool handles common issues:
- Invalid video formats
- API rate limits
- File upload failures
- Processing timeouts

All errors are returned with descriptive messages for debugging. 

# Gemini Video Analysis Features

This document outlines the advanced video analysis capabilities integrated into the HackReporter tool using Google's Gemini API.

## Features Overview

### 1. **Comprehensive Video Analysis**
- Full video content understanding and summarization
- Project demonstration analysis
- Technical feature extraction
- Team member identification (when shown/mentioned)
- Key moment timestamping

### 2. **Video Clipping Support**
- Analyze specific segments using start/end times (MM:SS format)
- Example: `start_time="01:30", end_time="02:45"`
- Focuses analysis on relevant portions of longer videos

### 3. **Custom Frame Rate Sampling**
- Adjustable FPS (frames per second) for analysis
- Default: 1 FPS for efficient processing
- Higher FPS for detailed motion analysis
- Lower FPS for static presentations

### 4. **Audio Transcription**
- Timestamped transcription of spoken content
- Synchronized with visual events
- Captures technical explanations and presentations

### 5. **Flexible File Handling**
- **Small files (<20MB)**: Processed inline for faster results
- **Large files (>20MB)**: Uploaded via File API with progress tracking
- Automatic cleanup of uploaded files

### 6. **Custom Analysis Prompts**
- Default hackathon-focused analysis
- Customizable prompts for specific needs
- Combines with transcription for comprehensive understanding

## Default Analysis Output

When analyzing hackathon videos, the tool provides:

1. **Project name and description**
2. **Key technical innovations and features**
3. **Team members** (if mentioned or shown)
4. **Most impressive technical achievements**
5. **Potential use cases and impact**
6. **Tweet-style summary** (280 chars max)
7. **Key timestamps** of important moments
8. **Technical challenges** mentioned
9. **Demo highlights** and visual elements

## Usage Examples

### Basic Video Analysis
```python
result = gemini_video_tool._run(
    video_path="demo.mp4"
)
```

### With Custom Prompt
```python
result = gemini_video_tool._run(
    video_path="demo.mp4",
    prompt="Focus on the AI/ML techniques demonstrated"
)
```

### Video Segment with Transcription
```python
result = gemini_video_tool._run(
    video_path="presentation.mp4",
    start_time="05:30",
    end_time="08:45",
    transcribe=True
)
```

### High-FPS Analysis
```python
result = gemini_video_tool._run(
    video_path="ui_demo.mp4",
    fps=5.0,  # 5 frames per second
    prompt="Analyze the UI/UX design elements"
)
```

## Technical Implementation

The tool uses Google's Gemini 2.0 Flash model with advanced video understanding capabilities:

- **Model**: `gemini-2.0-flash-001`
- **Max file size**: Unlimited (uses File API for >20MB)
- **Supported formats**: MP4, MOV, AVI, WEBM, and more
- **Processing**: Asynchronous with progress tracking

## Environment Setup

Required environment variable:
```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

## Error Handling

The tool includes comprehensive error handling for:
- Missing API keys
- Invalid video files
- Processing failures
- Network issues
- File size limitations

## Best Practices

1. **Use appropriate FPS**: Higher FPS for UI demos, lower for presentations
2. **Leverage clipping**: Focus on relevant segments in long videos
3. **Custom prompts**: Tailor analysis to specific aspects
4. **Transcription**: Enable for videos with important audio content
5. **File management**: The tool automatically cleans up uploaded files

## Migration to google-genai SDK

As of the latest update, the tool has been migrated from the deprecated `google.generativeai` package to the new `google-genai` SDK. This migration includes:

### Key Changes:
1. **Import statements**: 
   - Old: `import google.generativeai as genai`
   - New: `from google import genai` and `from google.genai import types`

2. **Client initialization**:
   - Old: `genai.configure(api_key=api_key)`
   - New: `client = genai.Client(api_key=api_key)`

3. **API calls**:
   - File upload: `client.files.upload()`
   - Content generation: `client.models.generate_content()`
   - File management: `client.files.get()`, `client.files.delete()`

4. **Content structure**:
   - Uses `types.Part.from_uri()` for uploaded files
   - Uses `types.Part.from_bytes()` for inline data
   - Uses `types.Part.from_text()` for text prompts

5. **Dependencies**:
   - Updated `pyproject.toml` and `requirements.txt` to use `google-genai>=1.0.0`

### Benefits:
- More stable and maintained API
- Better type hints and IDE support
- Improved error handling
- Consistent with Google's latest SDK architecture

This migration ensures the tool remains compatible with Google's latest APIs and continues to receive updates and support. 