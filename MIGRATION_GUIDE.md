# Migration from CrewAI to Simple Workflow

## What Changed

### Before (CrewAI Hell 😵)
```bash
# Complex setup with multiple config files
config/agents.yaml      # Agent configurations
config/tasks.yaml       # Task configurations
crew.py                 # 320 lines of crew orchestration
tools/                  # Multiple tool files with CrewAI wrappers

# Heavy dependencies
crewai>=0.141.0
crewai-tools>=0.51.1
agentops>=0.4.17
stagehand-py>=0.3.10
# ... and many more
```

### After (Simple & Clean ✨)
```bash
# Single script that just works
simple_workflow.py      # 300 lines of straightforward code
test_simple_workflow.py # Test script

# Minimal dependencies
google-genai>=1.0.0
litellm>=1.50.0
requests>=2.31.0
python-dotenv>=1.0.0
```

## How to Migrate

### 1. Update Dependencies
```bash
# Remove old dependencies
pip uninstall crewai crewai-tools agentops stagehand-py

# Install new minimal set
pip install -r requirements.txt
```

### 2. Update Environment Variables
```bash
# Copy the example
cp .env.example .env

# Edit with your keys (same as before)
GOOGLE_API_KEY=your_key
TYPEFULLY_API_KEY=your_key
OPENAI_API_KEY=your_key  # For litellm
```

### 3. Update Your Usage

#### Old Way:
```python
from crew import HackReporterCrew
import asyncio

async def main():
    crew = HackReporterCrew()
    # Complex crew orchestration...
    result = await process_videos("./videos")

asyncio.run(main())
```

#### New Way:
```bash
# Just run it
python simple_workflow.py ./videos

# Or with scheduling
python simple_workflow.py ./videos --schedule
```

### 4. Output Compatibility

The new workflow produces similar outputs but in a cleaner format:

| Old Output | New Output | Notes |
|------------|------------|-------|
| `output/tweet_thread.md` | `output/thread_content.txt` | Same content, simpler format |
| `output/video_summary_N.txt` | `output/analysis_N_videoname.json` | JSON format with more metadata |
| Complex crew results | `output/all_analyses.json` | All results in one file |

## What You Gain

### ✅ Simplicity
- One file to understand and modify
- No complex agent orchestration
- Direct API calls you can debug

### ✅ Reliability
- Fewer dependencies = fewer things that can break
- Better error handling
- Clearer error messages

### ✅ Performance
- No agent overhead
- Faster startup time
- More efficient API usage

### ✅ Maintainability
- Easy to customize prompts
- Simple to add new features
- Clear code structure

## What You Lose (Good Riddance!)

### ❌ CrewAI Complexity
- No more agent configuration files
- No more task orchestration debugging
- No more "why is my crew not working?" moments

### ❌ Unnecessary Abstractions
- Direct API calls instead of wrapped tools
- Simple functions instead of agent classes
- Straightforward async instead of crew processes

### ❌ Heavy Dependencies
- No more conflicting package versions
- No more mysterious import errors
- Faster installation and deployment

## Testing the Migration

```bash
# Test the new workflow
python test_simple_workflow.py

# Test with actual videos
python simple_workflow.py /path/to/your/videos

# Compare outputs with old system
diff output/thread_content.txt old_output/tweet_thread.md
```

## Rollback Plan

If you need to go back (but why would you?):

1. Keep the old `crew.py` file
2. Reinstall CrewAI dependencies: `pip install crewai crewai-tools`
3. Use the old workflow

But seriously, once you see how much simpler this is, you won't want to go back! 🎉

## Need Help?

The new code is so simple you can probably figure it out by reading it. But if you need to customize:

1. **Video analysis**: Edit the prompt in `VideoAnalyzer.analyze_video()`
2. **Thread generation**: Modify `ThreadCreator.create_thread_content()`
3. **Output format**: Change the file writing code in `SimpleWorkflow.process_videos()`

That's it! No more agent configurations, no more crew debugging, just code that works.