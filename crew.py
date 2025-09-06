# Lazy imports for better startup performance
from typing import List, TYPE_CHECKING
from pathlib import Path
import json
import asyncio
import os

if TYPE_CHECKING:
    from crewai.agents.agent_builder.base_agent import BaseAgent

# Import only when needed to reduce startup time
def _lazy_imports():
    from crewai import Agent, Crew, Process, Task
    from crewai.project import CrewBase, agent, crew, task
    from tools import GeminiVideoTool, TwitterSearchTool, TypefullyTool
    from tools.optimized_gemini_video_tool import OptimizedGeminiVideoTool
    from crewai_tools import StagehandTool
    from stagehand.schemas import AvailableModel
    from async_manager import processing_manager
    from performance_monitor import performance_monitor
    from cache_manager import cache_manager
    return Agent, Crew, Process, Task, CrewBase, agent, crew, task, GeminiVideoTool, TwitterSearchTool, TypefullyTool, OptimizedGeminiVideoTool, StagehandTool, AvailableModel, processing_manager, performance_monitor, cache_manager


# Get the imports when the class is defined
Agent, Crew, Process, Task, CrewBase, agent, crew, task, GeminiVideoTool, TwitterSearchTool, TypefullyTool, OptimizedGeminiVideoTool, StagehandTool, AvailableModel, processing_manager, performance_monitor, cache_manager = _lazy_imports()

@CrewBase
class HackReporterCrew():
    """HackReporter crew for processing hackathon videos and creating social media content"""

    agents: List['BaseAgent']
    tasks: List[Task]

    # All agents defined in one place
    @agent
    def video_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['video_summarizer'],  # type: ignore[index]
            tools=[OptimizedGeminiVideoTool()],
            verbose=True
        )

    @agent
    def person_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['person_finder'],  # type: ignore[index]
            tools=[
                StagehandTool(
                    api_key=os.environ["BROWSERBASE_API_KEY"],
                    project_id=os.environ["BROWSERBASE_PROJECT_ID"],
                    model_api_key=os.environ["OPENAI_API_KEY"],
                    model_name="gpt-5",
                ),
                # TwitterSearchTool()
            ],
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
    def team_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['team_research_task']  # type: ignore[index]
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
            agents=[self.video_summarizer(),
                    # self.person_finder() # Removed person finder for now
                    ],
            tasks=[
                self.video_analysis_task(),
                # self.team_research_task()  # Removed team_research_task for now
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


async def process_videos_optimized(directory: str, attendee_list: str | None = None) -> dict:
    """
    Optimized video processing with performance monitoring, caching, and better resource management.

    Args:
        directory: Path to directory containing video files
        attendee_list: Path to attendee list file (optional)

    Returns:
        Dictionary with processing results
    """
    # Start performance monitoring
    performance_monitor.start_monitoring()
    
    try:
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

        # Prepare video processing tasks
        processing_tasks = []
        for i, video_file in enumerate(video_files):
            absolute_path = video_file.resolve()
            file_size_mb = absolute_path.stat().st_size / (1024 * 1024)
            
            print(f"Preparing video {i+1}/{len(video_files)}: {video_file.name} ({file_size_mb:.1f}MB)")

            video_input = {
                'video_path': str(absolute_path),
                'video_filename': video_file.name,
                'attendee_list': attendee_list or 'Not provided'
            }

            # Create processing task
            task = processing_manager.add_task(
                task_id=f"video_{i+1}_{video_file.stem}",
                func=crew_instance.individual_crew().kickoff_async,
                video_input,
                priority=0,
                max_retries=2
            )
            processing_tasks.append(task)

        # Process videos with optimized async manager
        print(f"\n🚀 Processing {len(video_files)} videos with optimized async processing...")
        
        with performance_monitor.monitor_task("video_processing", sum(vf.stat().st_size for vf in video_files) / (1024 * 1024)):
            individual_results = await processing_manager.process_tasks(processing_tasks, timeout=1800)  # 30 min timeout

        # Count successful results
        successful_count = sum(1 for r in individual_results if not isinstance(r, Exception) and not str(r).startswith("Error"))
        print(f"\n✅ Processed {successful_count}/{len(individual_results)} videos successfully!")

        # Save individual results for aggregation
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        summaries = []
        for i, result in enumerate(individual_results):
            summary = ""
            
            if isinstance(result, Exception):
                summary = f"Error processing video: {str(result)}"
            elif isinstance(result, str) and result.startswith("Error"):
                summary = result
            else:
                try:
                    if hasattr(result, 'raw'):
                        summary = getattr(result, 'raw', str(result))
                    else:
                        summary = str(result)
                except Exception as e:
                    summary = f"Error extracting summary: {str(e)}"

            summaries.append(summary)

            # Save individual summary
            with open(output_dir / f'video_summary_{i+1}.txt', 'w') as f:
                f.write(summary)

        # Save all summaries for aggregation
        with open(output_dir / 'all_summaries.json', 'w') as f:
            json.dump(summaries, f, indent=2)

        # Run aggregation with monitoring
        print(f"\n🔄 Aggregating results and creating final tweet thread...")
        
        aggregation_inputs = {
            'all_summaries': '\n\n'.join(summaries),
            'video_count': len(video_files),
            'summaries_file': str(output_dir / 'all_summaries.json')
        }

        with performance_monitor.monitor_task("aggregation", len(aggregation_inputs['all_summaries']) / 1024):
            final_result = await crew_instance.aggregator_crew().kickoff_async(inputs=aggregation_inputs)

        # Save performance report
        performance_monitor.save_report("output/performance_report.json")
        
        # Get performance summary
        perf_summary = performance_monitor.get_summary()
        print(f"\n📊 Performance Summary:")
        print(f"  - Total processing time: {perf_summary.get('monitoring_duration', 0):.2f}s")
        print(f"  - Success rate: {perf_summary.get('tasks', {}).get('success_rate', 0)*100:.1f}%")
        print(f"  - Peak memory usage: {perf_summary.get('memory', {}).get('peak_mb', 0):.1f}MB")

        return {
            'processed_videos': len(video_files),
            'video_files': [str(vf) for vf in video_files],
            'individual_results': individual_results,
            'final_result': final_result,
            'performance_summary': perf_summary
        }

    finally:
        # Stop performance monitoring
        performance_monitor.stop_monitoring()
        processing_manager.cleanup()


# Keep the original function for backward compatibility
async def process_videos(directory: str, attendee_list: str | None = None) -> dict:
    """Original process_videos function - kept for backward compatibility"""
    return await process_videos_optimized(directory, attendee_list)
