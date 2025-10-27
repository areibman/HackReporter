# Simple Video Processor

A streamlined video understanding → tweet thread creation script that removes all CrewAI complexity and uses direct API calls with litellm.

## What it does

1. **Video Analysis**: Uses Google Gemini API to analyze hackathon project videos
2. **Thread Creation**: Uses litellm (OpenAI GPT-4o or Google Gemini) to create engaging tweet threads
3. **Output**: Saves to Typefully (if API key provided) and local files

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements_simple.txt
   ```

2. **Set environment variables**:
   ```bash
   export GOOGLE_API_KEY="your_google_api_key"
   export TYPEFULLY_API_KEY="your_typefully_api_key"  # Optional
   export OPENAI_API_KEY="your_openai_api_key"        # Optional (for better text generation)
   ```

## Usage

### Basic usage
```bash
python simple_video_processor.py /path/to/video/directory
```

### With options
```bash
# Process with max 3 concurrent videos
python simple_video_processor.py /path/to/videos --max-concurrent 3

# Process sequentially (useful for API quotas)
python simple_video_processor.py /path/to/videos --sequential
```

## How it works

1. **Video Discovery**: Finds all video files (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`) in the directory
2. **Parallel Processing**: Analyzes videos concurrently (configurable limit)
3. **Gemini Analysis**: Each video is uploaded to Gemini for comprehensive analysis
4. **Thread Generation**: All summaries are combined and fed to litellm to create an engaging tweet thread
5. **Output**: Thread is saved to Typefully (if configured) and local file

## Output

- **Console**: Real-time progress and final results
- **Typefully**: Draft created with shareable link (if API key provided)
- **Local File**: `output/tweet_thread_TIMESTAMP.md`

## Features

- ✅ **Simple**: No CrewAI complexity, just direct API calls
- ✅ **Fast**: Parallel video processing with configurable concurrency
- ✅ **Reliable**: Error handling and fallbacks
- ✅ **Flexible**: Works with or without Typefully/OpenAI APIs
- ✅ **Hackathon-focused**: Optimized prompts for project demos

## Example Output

```
🎬 Found 5 video files to process
🚀 Processing 5 videos with max 2 concurrent...
📹 Analyzing video: project_demo_1.mp4
📊 File size: 45.2MB
🔄 Uploading video to Gemini...
⏳ Waiting for video processing...
✅ Video processed successfully. Generating analysis...
✅ Analysis complete for project_demo_1.mp4
...

🧵 Creating tweet thread from 5 video summaries...
✅ Tweet thread created successfully!
✅ Typefully draft created! ID: 12345
🔗 Shareable link: https://typefully.com/share/abc123
💾 Thread saved to: output/tweet_thread_1703123456.md

🎉 PROCESSING COMPLETE
✅ Successfully processed 5/5 videos
📄 Thread saved to: output/tweet_thread_1703123456.md
🐦 Typefully draft created: 12345
```

## Troubleshooting

- **API Quotas**: Use `--sequential` flag to process videos one at a time
- **Large Videos**: The script handles large files but may take longer to upload
- **Missing APIs**: Script works with just Google API key, others are optional
- **Network Issues**: Built-in retry logic and error handling

## Migration from CrewAI

This simplified version replaces the complex CrewAI setup with:
- Direct Gemini API calls for video analysis
- litellm for text generation (OpenAI or Gemini)
- Simple async processing with semaphores
- No agent/task abstractions

Much cleaner and easier to understand! 🎉