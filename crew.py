from __future__ import annotations

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from litellm import completion
from tools import GeminiVideoTool


def _extract_litellm_content(response: Any) -> str:
    """Safely extract text content from a LiteLLM completion response."""
    try:
        # OpenAI-style object
        return response.choices[0].message.content  # type: ignore[attr-defined]
    except Exception:
        try:
            # Dict-style
            return response["choices"][0]["message"]["content"]  # type: ignore[index]
        except Exception:
            return str(response)


def analyze_video_with_gemini(video_path: str, transcribe: bool = True) -> str:
    """Analyze a single video using the existing Gemini video tool (direct Google API)."""
    tool = GeminiVideoTool()
    return tool._run(video_path=video_path, transcribe=transcribe)


def compose_thread_with_litellm(summaries: List[str]) -> str:
    """Create a tweet thread from video summaries using LiteLLM."""
    model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
    user_prompt = (
        "You are HackReporter. Convert the following hackathon video summaries into a concise, high-energy "
        "Twitter/X thread.\n\n"
        "Hard rules:\n"
        "- Only use information present in the provided summaries. Do not invent project names or details.\n"
        "- Include 1-2 standout highlights per project.\n"
        "- Number each tweet (1/, 2/, ...).\n"
        "- Keep each tweet under ~280 characters.\n"
        "- End with a short call-to-action.\n\n"
        f"Video summaries (count={len(summaries)}):\n\n"
        + "\n\n---\n\n".join(summaries)
    )

    try:
        response = completion(
            model=model_name,
            messages=[
                {"role": "system", "content": "Format your output as a ready-to-post Twitter thread."},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1200,
        )
        return _extract_litellm_content(response)
    except Exception as error:
        # Fallback: simple concatenation if LiteLLM is unavailable/misconfigured
        print(f"LiteLLM compose failed, using fallback: {error}")
        lines: List[str] = ["🚀 Hackathon Highlights"]
        for i, s in enumerate(summaries, start=1):
            snippet = (s or "").strip().splitlines()
            preview = " ".join(snippet[:3])[:240]
            lines.append(f"\n{i}/ {preview}")
        lines.append("\nThanks for following along! ✨")
        return "\n\n".join(lines)


async def process_videos(directory: str, attendee_list: str | None = None) -> Dict[str, Any]:
    """Simple pipeline: analyze videos -> compose thread (LiteLLM) -> write output."""
    video_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    video_dir = Path(directory)

    video_files: List[Path] = []
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f"*{ext}"))
        video_files.extend(video_dir.glob(f"*{ext.upper()}"))

    if not video_files:
        return {"error": f"No video files found in {directory}"}

    print(f"Found {len(video_files)} video files to process")

    # Analyze each video (sequential for simplicity and to avoid quota issues)
    summaries: List[str] = []
    individual_results: List[str] = []

    for idx, video_file in enumerate(video_files, start=1):
        absolute_path = video_file.resolve()
        print(f"\n📹 Analyzing video {idx}/{len(video_files)}: {video_file.name}")
        print(f"  Path: {absolute_path}")
        try:
            summary = analyze_video_with_gemini(str(absolute_path), transcribe=True)
        except Exception as e:
            summary = f"Error analyzing video {video_file.name}: {e}"
        summaries.append(summary)
        individual_results.append(summary)

    # Ensure output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Persist individual summaries
    for i, summary in enumerate(summaries, start=1):
        (output_dir / f"video_summary_{i}.txt").write_text(summary)

    (output_dir / "all_summaries.json").write_text(json.dumps(summaries, indent=2))

    # Compose final thread via LiteLLM
    print("\n🧵 Composing final tweet thread...")
    thread_text = compose_thread_with_litellm(summaries)
    (output_dir / "tweet_thread.md").write_text(thread_text)

    return {
        "processed_videos": len(video_files),
        "video_files": [str(v) for v in video_files],
        "individual_results": individual_results,
        "final_result": thread_text,
    }


class _AggregatorCrewShim:
    """Compatibility shim to support test_aggregation without CrewAI.

    Provides a .kickoff(inputs=...) method that composes a thread using LiteLLM
    and writes it to output/tweet_thread.md, returning the thread text.
    """

    def kickoff(self, inputs: Dict[str, Any]) -> str:
        all_summaries: str = inputs.get("all_summaries", "")
        if not isinstance(all_summaries, str):
            all_summaries = str(all_summaries)

        # Split summaries on double newlines separator used above, fallback to single block
        summaries: List[str] = [s for s in all_summaries.split("\n\n---\n\n") if s.strip()] or [all_summaries]

        thread_text = compose_thread_with_litellm(summaries)

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        (output_dir / "tweet_thread.md").write_text(thread_text)
        return thread_text


class HackReporterCrew:
    """Minimal wrapper exposing only aggregator_crew() for backward compatibility."""

    def aggregator_crew(self) -> _AggregatorCrewShim:
        return _AggregatorCrewShim()
