from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import List

try:
    from litellm import completion  # type: ignore
except Exception:  # ImportError or runtime errors
    completion = None  # type: ignore


def _summarize_single_video(video_path: str) -> str:
    """
    Use the existing Gemini video tool to analyze a single video and return a
    concise project summary block (4 lines) suitable for aggregation.
    """
    # Lazy import to avoid requiring google-genai unless video analysis is used
    from tools.gemini_video_tool import GeminiVideoTool
    result = tool._run(video_path=video_path, transcribe=True)
    return str(result)


def _generate_thread_with_litellm(project_summaries: List[str]) -> str:
    """
    Compose a Twitter/X thread using LiteLLM given a list of project summaries.
    Ensures EXACTLY 4 blank lines between tweets for Typefully compatibility.
    """
    summaries_text = "\n\n".join(project_summaries)
    video_count = len(project_summaries)

    system_prompt = "You are an expert social media editor. Output a Twitter/X thread with strict formatting."
    user_prompt = f"""
Create a Twitter/X thread from REAL hackathon project summaries below. RULES:
- Use ONLY the actual projects provided. Do NOT invent or add any projects.
- Start with a compelling 3-part intro (no numbering).
- Then write numbered tweets 1/, 2/, ... one per project.
- Keep each tweet concise and engaging.
- Use EXACTLY four blank lines between tweets (this is critical for Typefully).
- If there is only one project, include a single numbered tweet after the intro.

Input project summaries (count={video_count}):
---
{summaries_text}
---

Output format (strict):
[Intro line 1]

[Intro line 2]

[Intro line 3]




1/ [Project Name]

[One-line description]

[Tagline]
[@unknown]
"""

    model = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
    try:
        if completion is None:
            raise RuntimeError("litellm not available")
        resp = completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        content = resp.choices[0].message["content"] if hasattr(resp.choices[0], "message") else resp.choices[0]["message"]["content"]  # type: ignore[index]
        return content
    except Exception:
        # Deterministic fallback (no network/API keys required)
        intro = (
            "Join us as we unveil the groundbreaking projects from our latest hackathon! 🚀\n\n"
            "Innovation meets practical solutions in these exciting demonstrations.\n\n"
            "Discover the tools and ideas shaping tomorrow (🧵):\n\n\n\n\n"
        )

        def format_summary(idx: int, summary: str) -> str:
            lines = [l for l in summary.splitlines() if l.strip()]
            name = lines[0] if len(lines) > 0 else f"Project {idx}"
            description = lines[1] if len(lines) > 1 else "No description provided."
            tagline = lines[2] if len(lines) > 2 else ""
            handles = lines[3] if len(lines) > 3 else "@unknown"
            block = (
                f"{idx}/ {name}\n\n"
                f"{description}\n\n"
                f"{tagline}\n"
                f"{handles}"
            )
            return block

        parts: List[str] = [intro]
        for i, s in enumerate(project_summaries, start=1):
            parts.append(format_summary(i, s))
            # Ensure 4 blank lines between tweets except after last
            if i < len(project_summaries):
                parts.append("\n\n\n\n\n")
        return "".join(parts)


class HackReporterCrew:
    """
    Minimal shim kept for compatibility with existing scripts/tests.
    Provides an aggregator with a synchronous `kickoff` method and an
    individual video processor with an async `kickoff_async` method.
    """

    def aggregator_crew(self):
        class _Aggregator:
            def kickoff(self, inputs: dict) -> str:
                all_summaries = inputs.get("all_summaries", "")
                summaries_list = [s.strip() for s in all_summaries.split("\n\n") if s.strip()]
                thread_text = _generate_thread_with_litellm(summaries_list)
                out_dir = Path("output")
                out_dir.mkdir(exist_ok=True)
                (out_dir / "tweet_thread.md").write_text(thread_text)
                return thread_text

        return _Aggregator()

    def individual_crew(self):
        class _Individual:
            async def kickoff_async(self, inputs: dict) -> str:
                video_path = inputs.get("video_path")
                if not video_path:
                    return "Error: missing video_path"
                return await asyncio.to_thread(_summarize_single_video, video_path)

        return _Individual()


async def process_videos(directory: str, attendee_list: str | None = None) -> dict:
    """
    Simple pipeline: analyze videos with Gemini tool, then compose thread with LiteLLM.
    Writes final thread to output/tweet_thread.md.
    """
    video_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    video_dir = Path(directory)
    video_files: List[Path] = []
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f"*{ext}"))
        video_files.extend(video_dir.glob(f"*{ext.upper()}"))

    if not video_files:
        return {"error": f"No video files found in {directory}"}

    print(f"Found {len(video_files)} video files to process")

    # Limit concurrency to respect API quotas
    max_concurrent = int(os.getenv("MAX_CONCURRENT_VIDEOS", "2"))
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _run_one(idx: int, file_path: Path) -> str:
        async with semaphore:
            abs_path = file_path.resolve()
            print(f"Starting: {idx+1}/{len(video_files)} - {abs_path.name}")
            try:
                return await asyncio.to_thread(_summarize_single_video, str(abs_path))
            except Exception as e:
                return f"Error processing {abs_path.name}: {str(e)}"

    tasks = [_run_one(i, p) for i, p in enumerate(video_files)]
    individual_results: List[str] = list(await asyncio.gather(*tasks))

    # Persist individual summaries
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    summaries: List[str] = []
    for i, res in enumerate(individual_results, start=1):
        if isinstance(res, str):
            summaries.append(res)
        else:
            summaries.append(str(res))
        (output_dir / f"video_summary_{i}.txt").write_text(summaries[-1])

    (output_dir / "all_summaries.json").write_text(json.dumps(summaries, indent=2))

    # Compose final thread
    print("\nAggregating results and creating final tweet thread...")
    thread_text = _generate_thread_with_litellm(summaries)
    (output_dir / "tweet_thread.md").write_text(thread_text)

    return {
        "processed_videos": len(video_files),
        "video_files": [str(vf) for vf in video_files],
        "individual_results": individual_results,
        "final_result": thread_text,
    }
