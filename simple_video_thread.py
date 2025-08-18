import os
import sys
from pathlib import Path
from typing import List
import json
from datetime import datetime

import litellm  # Unified LLM interface – we will use it for all text generation
import openai   # Still needed for Whisper audio transcription
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment / API key setup
# ---------------------------------------------------------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY environment variable not found. Please set it in your .env file.")
    sys.exit(1)

openai.api_key = OPENAI_API_KEY

# You can override the text-generation model via env var. Defaults to gpt-4o.
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "openai/gpt-4o")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def transcribe_video(video_path: Path) -> str:
    """Transcribe the audio from a video using OpenAI Whisper.

    The OpenAI /audio/transcriptions endpoint accepts most common video formats
    (mp3, mp4, mpeg, mpga, m4a, wav, webm). We simply stream the file bytes.
    """
    print(f"🎙️  Transcribing audio for {video_path.name} …")
    with video_path.open("rb") as f:
        try:
            transcript_resp = openai.Audio.transcribe(
                model="whisper-1",
                file=f,
            )
            transcript_text: str = transcript_resp["text"]
            print(f"   ✅ Transcript length: {len(transcript_text):,} chars")
            return transcript_text
        except Exception as e:
            print(f"   ❌ Transcription failed: {e}")
            raise


def summarize_transcript(transcript: str, video_filename: str) -> str:
    """Summarise a single video transcript into a concise project summary."""
    print(f"📝 Summarising transcript for {video_filename} …")
    # Craft a focussed prompt – we keep it short to minimise tokens.
    system_prompt = (
        "You are a hackathon project summariser. Given a raw transcript of a project "
        "demo video, output a concise markdown summary containing: \n"
        "1. **Project name / elevator pitch** (max 280 chars) \n"
        "2. Key technical innovations and standout features (bullet list) \n"
        "3. Potential use-cases / impact (one paragraph) \n"
        "4. One tweet-style sentence (max 200 chars) describing why this is exciting."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcript},
    ]
    try:
        resp = litellm.completion(model=GENERATION_MODEL, messages=messages)
        summary = resp["choices"][0]["message"]["content"].strip()
        print(f"   ✅ Summary created (length {len(summary):,} chars)")
        return summary
    except Exception as e:
        print(f"   ❌ Summarisation failed: {e}")
        raise


def generate_twitter_thread(summaries: List[str]) -> str:
    """Combine individual summaries into an X/Twitter thread."""
    print("🧵 Generating Twitter/X thread …")
    joined_summaries = "\n\n".join(summaries)

    system_prompt = (
        "You are an expert social-media copywriter. Using the provided summaries of "
        "multiple hackathon projects, craft a vibrant Twitter/X thread that: \n"
        "• Opens with an engaging 1-tweet hook about the hackathon. \n"
        "• Dedicates one tweet per project, mentioning the project name and its key idea. \n"
        "• Keeps each tweet under 280 characters. \n"
        "• Separates individual tweets with **exactly four** newline characters so that "
        "they can be auto-split later (e.g. 'Tweet 1\n\n\n\nTweet 2'). \n"
        "• Ends with a closing call-to-action tweet."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Here are the project summaries:\n\n{joined_summaries}",
        },
    ]

    try:
        resp = litellm.completion(model=GENERATION_MODEL, messages=messages)
        thread = resp["choices"][0]["message"]["content"].strip()
        print(f"   ✅ Thread generated (length {len(thread):,} chars)")
        return thread
    except Exception as e:
        print(f"   ❌ Thread generation failed: {e}")
        raise

# ---------------------------------------------------------------------------
# Main processing routine
# ---------------------------------------------------------------------------

def process_videos(directory: Path) -> None:
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        sys.exit(1)

    video_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    video_files = [
        p for p in directory.iterdir() if p.suffix.lower() in [ext.lower() for ext in video_extensions]
    ]

    if not video_files:
        print("❌ No video files found to process.")
        sys.exit(1)

    print(f"📹 Found {len(video_files)} video(s) to process\n")

    summaries: List[str] = []

    for i, video_path in enumerate(sorted(video_files), start=1):
        print("-" * 60)
        print(f"[{i}/{len(video_files)}] {video_path.name}")
        try:
            transcript = transcribe_video(video_path)
            summary = summarize_transcript(transcript, video_path.name)
            summaries.append(summary)
        except Exception as e:
            print(f"⚠️  Skipping {video_path.name} due to error: {e}\n")
            continue

    if not summaries:
        print("❌ No summaries were generated. Exiting.")
        sys.exit(1)

    thread_text = generate_twitter_thread(summaries)

    # Write outputs
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    summaries_path = out_dir / f"video_summaries_{timestamp}.json"
    thread_path = out_dir / f"tweet_thread_{timestamp}.md"

    with summaries_path.open("w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
    with thread_path.open("w", encoding="utf-8") as f:
        f.write(thread_text)

    print("\n✅ All done!")
    print(f"   • Individual summaries saved to: {summaries_path}")
    print(f"   • Thread saved to:            {thread_path}")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_video_thread.py <video_directory>")
        sys.exit(1)

    videos_dir = Path(sys.argv[1])
    process_videos(videos_dir)