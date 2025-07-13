from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from pathlib import Path

from tools import GeminiVideoTool, CaptionsTool, TwitterSearchTool, TypefullyTool


@CrewBase
class HackReporterCrew():
    """HackReporter crew for processing hackathon videos and creating social media content"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def video_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['video_summarizer'],  # type: ignore[index]
            tools=[GeminiVideoTool(), TypefullyTool()],
            verbose=True
        )

    @agent
    def video_captioner(self) -> Agent:
        return Agent(
            config=self.agents_config['video_captioner'],  # type: ignore[index]
            tools=[CaptionsTool()],
            verbose=True
        )

    @agent
    def video_noise_remover(self) -> Agent:
        return Agent(
            config=self.agents_config['video_noise_remover'],  # type: ignore[index]
            tools=[CaptionsTool()],
            verbose=True
        )

    @agent
    def video_ranker(self) -> Agent:
        return Agent(
            config=self.agents_config['video_ranker'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def person_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['person_finder'],  # type: ignore[index]
            tools=[TwitterSearchTool()],
            verbose=True
        )

    @task
    def video_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_analysis_task']  # type: ignore[index]
        )

    @task
    def caption_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['caption_generation_task']  # type: ignore[index]
        )

    @task
    def audio_enhancement_task(self) -> Task:
        return Task(
            config=self.tasks_config['audio_enhancement_task']  # type: ignore[index]
        )

    @task
    def video_ranking_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_ranking_task']  # type: ignore[index]
        )

    @task
    def person_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['person_research_task']  # type: ignore[index]
        )

    @task
    def final_tweet_composition_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_tweet_composition_task'],  # type: ignore[index]
            output_file='output/tweet_thread.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HackReporter crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    def process_videos(self, directory: str, attendee_list: str | None = None) -> dict:
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

        # Process each video
        results = []
        for video_path in video_files:
            print(f"\nProcessing video: {video_path}")

            # Prepare inputs for the crew
            inputs = {
                'video_path': str(video_path),
                'video_directory': directory,
                'attendee_list': attendee_list or 'Not provided'
            }

            # Run the crew
            crew_result = self.crew().kickoff(inputs=inputs)

            results.append({
                'video': str(video_path),
                'result': crew_result
            })

        return {
            'processed_videos': len(results),
            'results': results
        }
