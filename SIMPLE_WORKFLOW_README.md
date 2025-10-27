# Simple Video Understanding → Thread Making Workflow

A streamlined, no-nonsense script that analyzes hackathon videos and creates engaging Twitter threads. **No CrewAI complexity** - just direct API calls that work.

## What This Does

1. **Video Analysis**: Uses Google Gemini API to analyze hackathon project videos
2. **Thread Creation**: Uses litellm to generate engaging Twitter thread content
3. **Publishing**: Creates drafts in Typefully (with optional auto-scheduling)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Required API Keys:**
   - `GOOGLE_API_KEY`: For video analysis with Gemini
   - `TYPEFULLY_API_KEY`: For creating tweet threads
   - `OPENAI_API_KEY`: For litellm thread generation (optional, can use other models)

## Usage

### Basic Usage
```bash
python simple_workflow.py /path/to/videos
```

### Auto-schedule the thread
```bash
python simple_workflow.py /path/to/videos --schedule
```

## What It Does

### 1. Video Analysis
- Uploads videos to Google Gemini API
- Extracts project details, technical highlights, team info
- Identifies key moments and quotable content
- Saves individual analysis files

### 2. Thread Generation
- Uses litellm to create engaging Twitter threads
- Highlights the most innovative projects
- Formats content for maximum engagement
- Keeps tweets under 280 characters

### 3. Publishing
- Creates drafts in Typefully
- Optionally schedules in next available slot
- Provides shareable links for review

## Output Files

All outputs are saved to the `output/` directory:
- `analysis_N_videoname.json`: Individual video analyses
- `all_analyses.json`: Combined analysis results
- `thread_content.txt`: Generated thread content
- `tweet_thread.md`: Final formatted thread (if using old workflow)

## API Models

The script uses:
- **Gemini 2.0 Flash** for video analysis (fast, cost-effective)
- **GPT-4** via litellm for thread generation (you can change this in the code)

## Compared to the Old CrewAI Workflow

| Old (CrewAI) | New (Simple) |
|--------------|--------------|
| 320 lines of complex agent orchestration | 300 lines of straightforward code |
| Multiple agents, tasks, and crews | Direct API calls |
| Complex configuration files | Simple environment variables |
| Heavy dependencies (crewai, stagehand, etc.) | Minimal dependencies |
| Difficult to debug and modify | Easy to understand and customize |

## Customization

Want to modify the analysis or thread generation? Just edit the prompts in `simple_workflow.py`:
- `VideoAnalyzer.analyze_video()`: Change the video analysis prompt
- `ThreadCreator.create_thread_content()`: Modify thread generation logic

## Error Handling

The script handles:
- Missing API keys
- Video processing failures
- API rate limits (with delays)
- Network errors
- File I/O issues

Failed videos are logged but don't stop the entire workflow.

## Performance

- **Sequential processing** to respect API rate limits
- **Automatic cleanup** of uploaded video files
- **Progress indicators** for long-running operations
- **Graceful error recovery** for individual failures

## Example Output

```
🚀 Starting Simple Video -> Thread Workflow
📁 Video directory: ./hackathon_videos
📅 Schedule thread: true
--------------------------------------------------
🎬 Found 3 videos to process

--- Processing video 1/3 ---
📹 Analyzing video: project_demo.mp4 (45.2MB)
⬆️  Uploading video to Gemini...
⏳ Processing video...
🤖 Generating analysis...
💾 Saved analysis to output/analysis_1_project_demo.json

🧵 Creating thread from 3 analyses...
🧵 Generating thread content with litellm...
💾 Thread content saved to output/thread_content.txt
📝 Creating Typefully draft...
✅ Draft created! ID: draft_123
🔗 Share: https://typefully.com/share/abc123
📅 Scheduled: 2024-01-15T10:00:00Z

🎉 Workflow completed successfully!
```

## Why This Is Better

- **Actually works** without fighting framework complexity
- **Easy to debug** when something goes wrong
- **Simple to modify** for your specific needs
- **Minimal dependencies** reduce maintenance burden
- **Direct API control** instead of abstraction layers

Just run it and get results. No more CrewAI headaches! 🎉