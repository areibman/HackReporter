"""
Optimized HackReporter Crew with performance improvements:
- Better async/parallel processing
- Memory optimization
- Caching for repeated operations
- Improved error handling
- Resource cleanup
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import asyncio
import os
import logging
from functools import lru_cache
from contextlib import asynccontextmanager
import gc
import tracemalloc

from tools import GeminiVideoTool, TwitterSearchTool, TypefullyTool
from crewai_tools import StagehandTool
from stagehand.schemas import AvailableModel

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable memory tracking in debug mode
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    tracemalloc.start()


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    async def __aenter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = asyncio.get_event_loop().time() - self.start_time
        logger.info(f"Operation completed in {elapsed:.2f} seconds")
        
        # Log memory usage if debug mode
        if os.getenv("DEBUG_MODE", "false").lower() == "true":
            current, peak = tracemalloc.get_traced_memory()
            logger.debug(f"Memory usage - Current: {current / 10**6:.1f}MB, Peak: {peak / 10**6:.1f}MB")


@CrewBase
class HackReporterCrew():
    """Optimized HackReporter crew for processing hackathon videos"""

    agents: List[BaseAgent]
    tasks: List[Task]
    
    # Cache for agent configurations
    _agent_cache: Dict[str, Agent] = {}
    
    @lru_cache(maxsize=1)
    def _get_tools(self) -> Dict[str, Any]:
        """Lazy load and cache tools to reduce memory usage"""
        tools = {
            'gemini': GeminiVideoTool(),
        }
        
        # Only load optional tools if API keys are present
        if os.environ.get("BROWSERBASE_API_KEY") and os.environ.get("BROWSERBASE_PROJECT_ID"):
            tools['stagehand'] = StagehandTool(
                api_key=os.environ["BROWSERBASE_API_KEY"],
                project_id=os.environ["BROWSERBASE_PROJECT_ID"],
                model_api_key=os.environ.get("OPENAI_API_KEY", ""),
                model_name=AvailableModel.GPT_4O,
            )
        
        if os.environ.get("TWITTER_API_KEY"):
            tools['twitter'] = TwitterSearchTool()
        
        if os.environ.get("TYPEFULLY_API_KEY"):
            tools['typefully'] = TypefullyTool()
            
        return tools

    @agent
    def video_summarizer(self) -> Agent:
        """Optimized video summarizer agent"""
        if 'video_summarizer' not in self._agent_cache:
            tools = self._get_tools()
            self._agent_cache['video_summarizer'] = Agent(
                config=self.agents_config['video_summarizer'],
                tools=[tools['gemini']],
                verbose=os.getenv("VERBOSE", "false").lower() == "true",
                max_iter=3,  # Limit iterations to prevent infinite loops
                memory=False  # Disable memory for single-task agents to save resources
            )
        return self._agent_cache['video_summarizer']

    @agent
    def person_finder(self) -> Agent:
        """Optimized person finder agent"""
        if 'person_finder' not in self._agent_cache:
            tools = self._get_tools()
            available_tools = []
            if 'stagehand' in tools:
                available_tools.append(tools['stagehand'])
            if 'twitter' in tools:
                available_tools.append(tools['twitter'])
                
            self._agent_cache['person_finder'] = Agent(
                config=self.agents_config['person_finder'],
                tools=available_tools,
                verbose=os.getenv("VERBOSE", "false").lower() == "true",
                max_iter=2,  # Limit iterations
                memory=False
            )
        return self._agent_cache['person_finder']

    @agent
    def thread_composer(self) -> Agent:
        """Optimized thread composer agent"""
        if 'thread_composer' not in self._agent_cache:
            tools = self._get_tools()
            available_tools = []
            if 'typefully' in tools:
                available_tools.append(tools['typefully'])
                
            self._agent_cache['thread_composer'] = Agent(
                config=self.agents_config['thread_composer'],
                tools=available_tools,
                verbose=os.getenv("VERBOSE", "false").lower() == "true",
                max_iter=2,
                memory=True  # Keep memory for aggregation tasks
            )
        return self._agent_cache['thread_composer']

    @agent
    def video_ranker(self) -> Agent:
        """Optimized video ranker agent"""
        if 'video_ranker' not in self._agent_cache:
            self._agent_cache['video_ranker'] = Agent(
                config=self.agents_config['video_ranker'],
                verbose=os.getenv("VERBOSE", "false").lower() == "true",
                max_iter=2,
                memory=False
            )
        return self._agent_cache['video_ranker']

    # Task definitions remain the same but with optimization hints
    @task
    def video_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_analysis_task'],
            async_execution=True  # Enable async execution
        )

    @task
    def person_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['person_research_task'],
            async_execution=True
        )

    @task
    def team_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['team_research_task'],
            async_execution=True
        )

    @task
    def create_tweet_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_tweet_summary_task'],
            async_execution=True
        )

    @task
    def aggregate_summaries_task(self) -> Task:
        return Task(
            config=self.tasks_config['aggregate_summaries_task']
        )

    @task
    def video_ranking_task(self) -> Task:
        return Task(
            config=self.tasks_config['video_ranking_task']
        )

    @task
    def final_tweet_composition_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_tweet_composition_task'],
            output_file='output/tweet_thread.md'
        )

    @crew
    def individual_crew(self) -> Crew:
        """Optimized crew for individual video processing"""
        return Crew(
            agents=[self.video_summarizer()],
            tasks=[self.video_analysis_task()],
            process=Process.sequential,
            verbose=os.getenv("VERBOSE", "false").lower() == "true",
            max_rpm=10,  # Rate limiting for API calls
            share_crew=False  # Don't share context between video processing
        )

    @crew
    def aggregator_crew(self) -> Crew:
        """Optimized crew for aggregating results"""
        return Crew(
            agents=[self.thread_composer(), self.video_ranker()],
            tasks=[
                self.aggregate_summaries_task(),
                self.video_ranking_task(),
                self.final_tweet_composition_task()
            ],
            process=Process.sequential,
            verbose=os.getenv("VERBOSE", "false").lower() == "true",
            share_crew=True  # Share context for aggregation
        )


class VideoProcessor:
    """Optimized video processor with better resource management"""
    
    def __init__(self, max_concurrent: int = None):
        self.max_concurrent = max_concurrent or int(os.getenv("MAX_CONCURRENT_VIDEOS", "3"))
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.results_cache = {}
        
    @asynccontextmanager
    async def process_with_cleanup(self, video_input: Dict, index: int):
        """Process video with automatic resource cleanup"""
        try:
            async with self.semaphore:
                logger.info(f"Processing video {index+1}: {video_input['video_filename']}")
                crew_instance = HackReporterCrew()
                yield crew_instance
        finally:
            # Force garbage collection after each video to free memory
            gc.collect()
            
    async def process_single_video(self, video_input: Dict, index: int) -> Any:
        """Process a single video with error handling and retries"""
        max_retries = int(os.getenv("MAX_RETRIES", "2"))
        retry_delay = int(os.getenv("RETRY_DELAY", "5"))
        
        for attempt in range(max_retries):
            try:
                async with self.process_with_cleanup(video_input, index) as crew_instance:
                    async with PerformanceMonitor():
                        result = await crew_instance.individual_crew().kickoff_async(inputs=video_input)
                        logger.info(f"✅ Completed video {index+1}: {video_input['video_filename']}")
                        return result
                        
            except Exception as e:
                logger.error(f"Attempt {attempt+1} failed for video {index+1}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    return f"Error processing {video_input['video_filename']}: {str(e)}"
    
    async def process_batch(self, video_inputs: List[Dict]) -> List[Any]:
        """Process videos in optimized batches"""
        # Split into batches for better memory management
        batch_size = int(os.getenv("BATCH_SIZE", "5"))
        results = []
        
        for i in range(0, len(video_inputs), batch_size):
            batch = video_inputs[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} videos)")
            
            tasks = [
                self.process_single_video(video_input, i+j)
                for j, video_input in enumerate(batch)
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Add delay between batches to respect API limits
            if i + batch_size < len(video_inputs):
                delay = int(os.getenv("BATCH_DELAY", "10"))
                logger.info(f"Waiting {delay}s before next batch...")
                await asyncio.sleep(delay)
                
        return results


async def process_videos_optimized(directory: str, attendee_list: Optional[str] = None) -> Dict:
    """
    Optimized video processing with better performance and resource management
    """
    async with PerformanceMonitor():
        # Find video files
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        video_dir = Path(directory)
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(video_dir.glob(f'*{ext}'))
            video_files.extend(video_dir.glob(f'*{ext.upper()}'))
        
        if not video_files:
            return {"error": f"No video files found in {directory}"}
        
        logger.info(f"Found {len(video_files)} video files to process")
        
        # Prepare inputs
        video_inputs = []
        for video_file in video_files:
            absolute_path = video_file.resolve()
            
            # Skip very large files if configured
            max_size_mb = int(os.getenv("MAX_VIDEO_SIZE_MB", "500"))
            file_size_mb = absolute_path.stat().st_size / (1024*1024)
            
            if file_size_mb > max_size_mb:
                logger.warning(f"Skipping {video_file.name} - size {file_size_mb:.1f}MB exceeds limit")
                continue
                
            video_inputs.append({
                'video_path': str(absolute_path),
                'video_filename': video_file.name,
                'attendee_list': attendee_list or 'Not provided'
            })
        
        # Process videos with optimized processor
        processor = VideoProcessor()
        
        # Choose processing mode based on configuration
        if os.getenv("SEQUENTIAL_VIDEO_PROCESSING", "false").lower() == "true":
            logger.info("Running in SEQUENTIAL mode")
            individual_results = []
            for i, video_input in enumerate(video_inputs):
                result = await processor.process_single_video(video_input, i)
                individual_results.append(result)
                if i < len(video_inputs) - 1:
                    await asyncio.sleep(3)
        else:
            logger.info(f"Running in PARALLEL mode (max {processor.max_concurrent} concurrent)")
            individual_results = await processor.process_batch(video_inputs)
        
        # Save results
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        summaries = []
        for i, result in enumerate(individual_results):
            summary = extract_summary(result)
            summaries.append(summary)
            
            # Save individual summary
            with open(output_dir / f'video_summary_{i+1}.txt', 'w') as f:
                f.write(summary)
        
        # Save all summaries
        with open(output_dir / 'all_summaries.json', 'w') as f:
            json.dump(summaries, f, indent=2)
        
        # Aggregate results
        logger.info("Aggregating results and creating final tweet thread...")
        crew_instance = HackReporterCrew()
        
        aggregation_inputs = {
            'all_summaries': '\n\n'.join(summaries),
            'video_count': len(video_files),
            'summaries_file': str(output_dir / 'all_summaries.json')
        }
        
        final_result = await crew_instance.aggregator_crew().kickoff_async(inputs=aggregation_inputs)
        
        return {
            'processed_videos': len(video_files),
            'video_files': [str(vf) for vf in video_files],
            'individual_results': individual_results,
            'final_result': final_result
        }


def extract_summary(result: Any) -> str:
    """Extract summary from result object with error handling"""
    if isinstance(result, Exception):
        return f"Error processing video: {str(result)}"
    elif isinstance(result, str) and result.startswith("Error"):
        return result
    else:
        try:
            if hasattr(result, 'raw'):
                return getattr(result, 'raw', str(result))
            else:
                return str(result)
        except Exception as e:
            return f"Error extracting summary: {str(e)}"


# Export the optimized function
process_videos = process_videos_optimized