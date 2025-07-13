# HackReporter
Automated hackathon twitter recap agents powered by CrewAI

## Overview
HackReporter uses CrewAI to orchestrate multiple AI agents that work together to:
1. Analyze hackathon project videos
2. Generate captions and enhance audio
3. Find participant social media profiles using Exa Deep Search AI
4. Create engaging Twitter/X threads
5. Rank videos by engagement potential
6. **Automatically create drafts in Typefully** for easy scheduling and posting

## MCP Tools
- **kickoff_hackathon_reporter**: Process videos in a directory and generate tweet threads
  - Automatically creates a draft in Typefully after thread generation
  - Provides shareable link for review before posting
- **create_tweet_thread**: Post generated threads via Typefully API (manual trigger)

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
EXA_API_KEY=your_exa_api_key  # Get from https://exa.ai/
CAPTIONS_AI_API_KEY=your_captions_key

# Typefully API for creating tweet drafts
TYPEFULLY_API_KEY=your_typefully_key  # Get from Typefully settings
```

#### Getting Your Typefully API Key:
1. Log in to your [Typefully](https://typefully.com) account
2. Go to Settings → Integrations
3. Switch to the Twitter/X account you want to use
4. Generate or copy your API key for that account
5. Add it to your `.env` file

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

## Typefully Integration

HackReporter automatically creates drafts in Typefully after processing videos:

### How It Works:
1. **Video Processing**: The crew analyzes all videos in the specified directory
2. **Thread Generation**: Creates a complete Twitter/X thread with:
   - Engaging 3-section title
   - Individual tweets for each project
   - Proper mentions and hashtags
   - Thread numbering (1/, 2/, etc.)
   - **Important**: Each tweet is separated by 4 blank lines for proper thread splitting
3. **Typefully Draft**: Automatically creates a draft using the Typefully API
   - Auto-splits the thread at the 4-newline boundaries
   - Generates a shareable link for review
   - Ready to schedule or publish directly from Typefully

### Benefits:
- **Review Before Posting**: Check the thread formatting in Typefully's preview
- **Easy Scheduling**: Use Typefully's scheduling features
- **Media Attachments**: Add videos/images to specific tweets in Typefully
- **Analytics**: Track performance through Typefully's analytics

### Output:
After processing, you'll receive:
- Tweet thread saved to `output/tweet_thread.md` (with proper 4-newline formatting)
- Example formatting available in `output/example_formatted_thread.md`
- Typefully draft ID and shareable link in the console
- Confirmation of successful draft creation

## Enhanced Twitter/X Profile Search

The HackReporter now uses Exa's Deep Search API for intelligent Twitter/X handle discovery:

### Key Features:
- **Multiple Name Search**: Can search for entire teams at once
- **Company & Tech Handles**: Automatically finds official accounts for mentioned technologies
- **Context-Aware**: Works even without specific names by analyzing project context
- **Graceful Fallbacks**: Handles cases where profiles can't be found

### Testing the Twitter Search:
```bash
# Run the test script to see examples
python test_twitter_search.py
```

The tool intelligently handles:
1. **Missing Names**: Uses project context to suggest relevant handles
2. **Multiple Team Members**: Searches for all team members in one go
3. **Tech Stack**: Finds official handles for frameworks, tools, and companies mentioned

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
- Goal: Given the attendee list, do a deep research to find Twitter/X handles for people, companies, and technologies
- Tools:
    - **Exa Deep Search API**: Advanced AI-powered search for finding social media profiles
    - Features:
        - Handles multiple team members in a single search
        - Finds company and technology official accounts
        - Works even when names aren't available (uses context)
        - Gracefully handles cases where profiles can't be found
        - Assumes tech industry context for better results