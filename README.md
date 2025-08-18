# Video to Twitter Thread Generator

A simple, straightforward tool that analyzes hackathon videos and generates engaging Twitter threads. No complex frameworks - just clean Python with litellm and Google Gemini.

## Features

- 🎥 **Video Analysis**: Uses Google Gemini to understand video content
- 🧵 **Thread Generation**: Creates engaging Twitter threads using LLMs (GPT-4, Claude, etc.)
- 📝 **Typefully Integration**: Optional direct publishing to Typefully
- ⚡ **Parallel Processing**: Analyzes multiple videos concurrently
- 🎯 **Simple & Clean**: No unnecessary complexity or framework overhead

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-name>

# Install dependencies
pip install -r requirements.txt
```

## Setup

Create a `.env` file with your API keys:

```env
# Required
GOOGLE_API_KEY=your_google_api_key_here

# For GPT models (default)
OPENAI_API_KEY=your_openai_api_key_here

# For Claude models (optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# For Typefully publishing (optional)
TYPEFULLY_API_KEY=your_typefully_api_key_here
```

## Usage

### Basic Usage

Analyze videos in a directory and generate a Twitter thread:

```bash
python video_to_thread.py /path/to/videos/
```

### Advanced Options

```bash
# Use a different model (default is gpt-4o)
python video_to_thread.py /path/to/videos/ --model claude-3-opus-20240229

# Create a draft in Typefully
python video_to_thread.py /path/to/videos/ --typefully

# Combine options
python video_to_thread.py /path/to/videos/ --model gpt-4-turbo --typefully
```

### Supported Models

You can use any model supported by litellm:
- OpenAI: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Anthropic: `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- And many more (see [litellm docs](https://docs.litellm.ai/docs/providers))

## Output

The script generates:
- `output/video_analyses.json` - Detailed analysis of each video
- `output/twitter_thread.txt` - The generated Twitter thread

## How It Works

1. **Video Discovery**: Finds all video files in the specified directory
2. **Video Analysis**: Each video is uploaded to Google Gemini for analysis
3. **Information Extraction**: Extracts project details, features, team info, etc.
4. **Thread Composition**: Uses your chosen LLM to create an engaging thread
5. **Optional Publishing**: Can create a draft in Typefully

## Architecture

Simple and straightforward:

```
video_to_thread.py
├── VideoAnalyzer     # Handles Gemini video analysis
├── ThreadComposer    # Creates threads using litellm
└── TypefullyPublisher # Optional Typefully integration
```

No agents, no crews, no complex orchestration - just functions that do their job.

## Requirements

- Python 3.8+
- Google Cloud API key with Gemini access
- OpenAI/Anthropic API key for thread generation
- (Optional) Typefully API key for publishing

## License

MIT