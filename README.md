# HackReporter
Automated hackathon twitter recap agents powered by CrewAI

## Overview
HackReporter uses CrewAI to orchestrate multiple AI agents that work together to:
1. Analyze hackathon project videos
2. Generate captions and enhance audio
3. Find participant social media profiles
4. Create engaging Twitter/X threads
5. Rank videos by engagement potential

## MCP Tools
- **kickoff_hackathon_reporter**: Process videos in a directory and generate tweet threads
- **create_tweet_thread**: Post generated threads via Typefully API (https://support.typefully.com/en/articles/8718287-typefully-api)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
# or use uv:
uv pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file with:
```bash
# AgentOps for monitoring and observability
AGENTOPS_API_KEY=your_agentops_api_key  # Get from https://www.agentops.ai/

# LLM and API Keys
GOOGLE_API_KEY=your_google_api_key
TWITTER_BEARER_TOKEN=your_twitter_token
CAPTIONS_AI_API_KEY=your_captions_key
TYPEFULLY_API_KEY=your_typefully_key
```

### 3. Run the MCP Server
```bash
python server.py
```

### 4. Use the Tools
```python
# Process videos
kickoff_hackathon_reporter(
    directory="/path/to/video/directory",
    attendee_list="/path/to/attendees.csv"  # optional
)

# Create tweet thread
create_tweet_thread(tweet_file="output/tweet_thread.md")
```

## Monitoring with AgentOps

HackReporter is integrated with [AgentOps](https://www.agentops.ai/) for comprehensive monitoring and observability of your AI agents.

### What AgentOps Provides:
- **Trace Visualization**: See how your CrewAI agents work together in real-time
- **Performance Metrics**: Track processing time, token usage, and costs
- **Error Monitoring**: Identify and debug issues in your agent workflows
- **Session Recording**: Replay entire video processing sessions
- **LLM Call Tracking**: Monitor all LLM interactions automatically

### Accessing Your Traces:
1. Sign up at [https://www.agentops.ai/](https://www.agentops.ai/)
2. Get your API key from the settings page
3. Add it to your `.env` file as `AGENTOPS_API_KEY`
4. Run the HackReporter - each video processing session will create a new trace
5. View your traces in the AgentOps dashboard

Each trace will be named after the directory being processed and tagged with relevant metadata for easy filtering.

## CrewAI Implementation

Agent:
- Role: Video Summarizer
- Goal: Take the content of the video and summarize in in the following tweet style. Here are the examples:
- Tools:
    - Gemini Video API: https://ai.google.dev/gemini-api/docs/video-understanding
    - Features:
        - Automatic handling of video files (inline for <20MB, File API for larger)
        - Audio transcription with timestamps
        - Video clipping (specify start/end times)
        - Custom frame rate sampling (default: 1 FPS)
        - Visual description at key moments
        - Support for mp4, mov, avi, webm, and more formats

Agent:
- Role: Video Captioner
- Goal: Add captions to the video and spellchecks them
- Tools:
    - captions.ai: https://www.captions.ai/add-subtitles

Agent:
- Role: Video Background Noise Remover
- Goal: Remove background noise from the video
- Tools:
    - captions.ai: https://www.captions.ai/add-subtitles

Agent:
- Role: Video Ranker
- Goal: Rank the videos by how interesting they would be to an audience

Agent:
- Role: Person Finder
- Goal: Given the attendee list, do a deep research on twitter API to find the person and/or find their luma info and tie it to them
- Tools:
    - Twitter API: https://developer.x.com/en/docs/x-api