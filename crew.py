from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from pathlib import Path
import json
import asyncio

from tools import GeminiVideoTool, TwitterSearchTool, TypefullyTool


@CrewBase
class HackReporterCrew():
    """HackReporter crew for processing hackathon videos and creating social media content"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # All agents defined in one place
    @agent
    def video_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['video_summarizer'],  # type: ignore[index]
            tools=[GeminiVideoTool()],
            verbose=True
        )

    @agent
    def person_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['person_finder'],  # type: ignore[index]
            tools=[TwitterSearchTool()],
            verbose=True
        )

    @agent
    def thread_composer(self) -> Agent:
        return Agent(
            config=self.agents_config['thread_composer'],  # type: ignore[index]
            tools=[TypefullyTool()],
            verbose=True
        )

    @agent
    def video_ranker(self) -> Agent:
        return Agent(
            config=self.agents_config['video_ranker'],  # type: ignore[index]
            verbose=True
        )

    # Individual video processing tasks
    @task
    def video_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_analysis_task']  # type: ignore[index]
        )

    @task
    def person_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['person_research_task']  # type: ignore[index]
        )

    @task
    def create_tweet_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_tweet_summary_task']  # type: ignore[index]
        )

    # Aggregation tasks
    @task
    def aggregate_summaries_task(self) -> Task:
        return Task(
            config=self.tasks_config['aggregate_summaries_task']  # type: ignore[index]
        )

    @task
    def video_ranking_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_ranking_task']  # type: ignore[index]
        )

    @task
    def final_tweet_composition_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_tweet_composition_task'],  # type: ignore[index]
            output_file='output/tweet_thread.md'
        )

    @crew
    def individual_crew(self) -> Crew:
        """Creates the crew for individual video processing"""
        return Crew(
            agents=[self.video_summarizer(), self.person_finder()],
            tasks=[
                self.video_analysis_task(),
                self.person_research_task(),
                self.create_tweet_summary_task()
            ],
            process=Process.sequential,
            verbose=True,
        )

    @crew
    def aggregator_crew(self) -> Crew:
        """Creates the crew for aggregating results"""
        return Crew(
            agents=[self.thread_composer(), self.video_ranker()],
            tasks=[
                self.aggregate_summaries_task(),
                self.video_ranking_task(),
                self.final_tweet_composition_task()
            ],
            process=Process.sequential,
            verbose=True,
        )


async def process_videos(directory: str, attendee_list: str | None = None) -> dict:
    """
    Process all videos in a directory and generate social media content.

    Args:
        directory: Path to directory containing video files
        attendee_list: Path to attendee list file (optional)

    Returns:
        Dictionary with processing results
    """
    # Find all video files in directory
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    video_dir = Path(directory)
    video_files = []

    for ext in video_extensions:
        video_files.extend(video_dir.glob(f'*{ext}'))
        video_files.extend(video_dir.glob(f'*{ext.upper()}'))

    if not video_files:
        return {"error": f"No video files found in {directory}"}

    print(f"Found {len(video_files)} video files to process")

    # Create the crew instance
    crew_instance = HackReporterCrew()

    # First, process each video individually using kickoff_for_each
    # Prepare inputs for each video
    video_inputs = []
    for video_file in video_files:
        # Use absolute path to ensure agent can find the file
        absolute_path = video_file.resolve()
        print(f"\nDEBUG - Processing video: {video_file.name}")
        print(f"  Absolute path: {absolute_path}")
        print(f"  File exists: {absolute_path.exists()}")
        print(f"  File size: {absolute_path.stat().st_size / (1024*1024):.1f}MB")

        video_inputs.append({
            'video_path': str(absolute_path),
            'video_filename': video_file.name,
            'attendee_list': attendee_list or 'Not provided'
        })

    # Process videos individually using the individual_crew configuration
    print(f"\nProcessing {len(video_files)} videos individually...")
    individual_results = await crew_instance.individual_crew().kickoff_for_each_async(inputs=video_inputs)

    # Save individual results for aggregation
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    summaries = []
    for i, result in enumerate(individual_results):
        print(f"\nDEBUG - Processing result {i+1}:")
        print(f"  Result type: {type(result)}")
        print(f"  Has 'raw' attribute: {hasattr(result, 'raw')}")

        # Extract the summary from the result
        if hasattr(result, 'raw'):
            summary = result.raw
        else:
            summary = str(result)

        print(f"  Summary length: {len(summary)} chars")
        print(f"  First 100 chars: {summary[:100]}...")

        summaries.append(summary)

        # Save individual summary
        with open(output_dir / f'video_summary_{i+1}.txt', 'w') as f:
            f.write(summary)

    # Save all summaries for aggregation
    with open(output_dir / 'all_summaries.json', 'w') as f:
        json.dump(summaries, f, indent=2)

    # Now run the aggregator crew configuration
    print(f"\nAggregating results and creating final tweet thread...")

    # Debug: Show what summaries we're passing
    print(f"\nDEBUG - Summaries being passed to aggregator:")
    print(f"Number of summaries: {len(summaries)}")
    for i, summary in enumerate(summaries):
        print(f"\nSummary {i+1}:")
        print(summary)
        print("-" * 50)

    aggregation_inputs = {
        'all_summaries': '\n\n'.join(summaries),
        'video_count': len(video_files),
        'summaries_file': str(output_dir / 'all_summaries.json')
    }

    print(f"\nDEBUG - Aggregation inputs:")
    print(f"- all_summaries length: {len(aggregation_inputs['all_summaries'])} chars")
    print(f"- video_count: {aggregation_inputs['video_count']}")
    print(f"- summaries_file: {aggregation_inputs['summaries_file']}")

    final_result = await crew_instance.aggregator_crew().kickoff_async(inputs=aggregation_inputs)

    return {
        'processed_videos': len(video_files),
        'video_files': [str(vf) for vf in video_files],
        'individual_results': individual_results,
        'final_result': final_result
    }
