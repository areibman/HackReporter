# HackReporter CrewAI Architecture

## Overview

HackReporter uses CrewAI to orchestrate multiple AI agents that work together to process hackathon videos and create engaging social media content. The system is designed with 5 specialized agents, each with specific roles and tools.

## Agents

### 1. Video Summarizer
- **Role**: Senior Video Content Summarizer
- **Goal**: Extract key moments and create tweet-style summaries
- **Tools**: Gemini Video API (for analyzing video content)
- **Tasks**: 
  - Video analysis and content extraction
  - Final tweet composition

### 2. Video Ranker
- **Role**: Content Strategist and Engagement Analyst
- **Goal**: Rank videos by audience interest potential
- **Tools**: None (uses analysis from other agents)
- **Tasks**: Video ranking based on engagement potential

### 3. Person Finder
- **Role**: Social Media Research Specialist
- **Goal**: Find attendee social media profiles
- **Tools**: Twitter/X API
- **Tasks**: Research participants and find their social handles

## Workflow

The agents work in a sequential process:

1. **Video Analysis**: The Video Summarizer analyzes each video to extract project information
2. **Caption Generation**: The Video Captioner adds accurate subtitles
3. **Audio Enhancement**: The Background Noise Remover cleans up the audio
4. **Video Ranking**: The Video Ranker assesses engagement potential
5. **Person Research**: The Person Finder identifies participants' social profiles
6. **Tweet Composition**: The Video Summarizer creates the final tweet thread

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
# or
uv pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file with the following:

```bash
# Google API Key for Gemini Video Analysis
GOOGLE_API_KEY=your_google_api_key_here

# Twitter/X API Bearer Token
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# Captions.ai API Key (if available)
CAPTIONS_AI_API_KEY=your_captions_ai_api_key_here

# Typefully API Key
TYPEFULLY_API_KEY=your_typefully_api_key_here
```

### 3. Run the MCP Server

```bash
python server.py
```

### 4. Use the MCP Tools

The server exposes two main tools:

#### kickoff_hackathon_reporter
```python
kickoff_hackathon_reporter(
    directory="/path/to/videos",
    attendee_list="/path/to/attendees.csv"  # optional
)
```

#### create_tweet_thread
```python
create_tweet_thread(
    tweet_file="output/tweet_thread.md"
)
```

## File Structure

```
src/hackreporter/
├── config/
│   ├── agents.yaml      # Agent definitions
│   └── tasks.yaml       # Task definitions
├── tools/
│   ├── gemini_video_tool.py
│   ├── captions_tool.py
│   └── twitter_tool.py
├── crew.py              # Main crew orchestration
└── __init__.py

output/                  # Generated tweet threads
```

## Customization

### Modifying Agents
Edit `src/hackreporter/config/agents.yaml` to change agent personalities, goals, or backstories.

### Modifying Tasks
Edit `src/hackreporter/config/tasks.yaml` to change task descriptions or expected outputs.

### Adding New Tools
1. Create a new tool in `src/hackreporter/tools/`
2. Import it in `src/hackreporter/tools/__init__.py`
3. Add it to the relevant agent in `crew.py`

## API Integration Notes

### Gemini Video API
- Requires Google Cloud API key
- Supports advanced video understanding features:
  - Automatic file size handling (inline for <20MB, File API for larger)
  - Video clipping with start/end timestamps
  - Custom frame rate sampling (default: 1 FPS)
  - Audio transcription with timestamps
  - Visual descriptions at key moments
  - Support for multiple video formats (mp4, mov, avi, webm, etc.)
- Token usage: ~300 tokens per second at default resolution
- Used for extracting project information, demos, and creating summaries

### Twitter/X API
- Requires Bearer Token for v2 API
- Used for searching user profiles
- Rate limits apply

### Captions.ai
- Currently implemented as mock (no public API)
- Would require either:
  - Official API access
  - Web automation solution
  - Manual processing workflow

### Typefully API
- API documentation: https://support.typefully.com/en/articles/8718287-typefully-api
- Integration pending implementation 