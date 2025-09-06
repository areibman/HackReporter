"""
Async processing manager for optimized video processing
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from pathlib import Path
import signal
import sys

logger = logging.getLogger(__name__)


@dataclass
class ProcessingTask:
    """Represents a processing task"""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    created_at: float = 0.0
    retries: int = 0
    max_retries: int = 3


class AsyncProcessingManager:
    """Manages async processing with rate limiting, retries, and resource management"""
    
    def __init__(self, max_concurrent: int = 2, rate_limit_per_minute: int = 10):
        """
        Initialize async processing manager
        
        Args:
            max_concurrent: Maximum number of concurrent tasks
            rate_limit_per_minute: Maximum API calls per minute
        """
        self.max_concurrent = max_concurrent
        self.rate_limit_per_minute = rate_limit_per_minute
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = asyncio.Semaphore(rate_limit_per_minute)
        self.rate_limit_reset_time = time.time() + 60
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[ProcessingTask] = []
        self.failed_tasks: List[ProcessingTask] = []
        
        # Performance metrics
        self.start_time = None
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks_count = 0
        
    async def _reset_rate_limit(self):
        """Reset rate limiter every minute"""
        while True:
            await asyncio.sleep(60)
            self.rate_limiter = asyncio.Semaphore(self.rate_limit_per_minute)
            self.rate_limit_reset_time = time.time() + 60
            logger.debug("Rate limiter reset")
    
    async def _process_single_task(self, task: ProcessingTask) -> Any:
        """Process a single task with error handling and retries"""
        task_id = task.id
        
        try:
            # Apply rate limiting
            async with self.rate_limiter:
                # Apply concurrency limiting
                async with self.semaphore:
                    logger.info(f"Processing task {task_id}")
                    
                    # Execute the task
                    if asyncio.iscoroutinefunction(task.func):
                        result = await task.func(*task.args, **task.kwargs)
                    else:
                        # Run sync function in thread pool
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(None, task.func, *task.args, **task.kwargs)
                    
                    logger.info(f"Completed task {task_id}")
                    return result
                    
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            
            # Retry logic
            if task.retries < task.max_retries:
                task.retries += 1
                logger.info(f"Retrying task {task_id} (attempt {task.retries + 1}/{task.max_retries + 1})")
                
                # Exponential backoff
                wait_time = min(2 ** task.retries, 30)  # Max 30 seconds
                await asyncio.sleep(wait_time)
                
                return await self._process_single_task(task)
            else:
                logger.error(f"Task {task_id} failed after {task.max_retries + 1} attempts")
                raise e
    
    async def add_task(
        self, 
        task_id: str, 
        func: Callable, 
        *args, 
        priority: int = 0,
        max_retries: int = 3,
        **kwargs
    ) -> ProcessingTask:
        """Add a task to the processing queue"""
        task = ProcessingTask(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            created_at=time.time(),
            max_retries=max_retries
        )
        
        self.total_tasks += 1
        logger.debug(f"Added task {task_id} to queue")
        return task
    
    async def process_tasks(self, tasks: List[ProcessingTask], timeout: Optional[float] = None) -> List[Any]:
        """
        Process a list of tasks concurrently
        
        Args:
            tasks: List of tasks to process
            timeout: Optional timeout in seconds
            
        Returns:
            List of results in the same order as tasks
        """
        if not tasks:
            return []
        
        self.start_time = time.time()
        logger.info(f"Starting processing of {len(tasks)} tasks with max {self.max_concurrent} concurrent")
        
        # Start rate limiter reset task
        rate_limiter_task = asyncio.create_task(self._reset_rate_limit())
        
        try:
            # Create tasks with proper error handling
            async def safe_process_task(task):
                try:
                    return await self._process_single_task(task)
                except Exception as e:
                    logger.error(f"Task {task.id} failed permanently: {str(e)}")
                    self.failed_tasks_count += 1
                    return f"Error processing {task.id}: {str(e)}"
            
            # Process all tasks concurrently
            if timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*[safe_process_task(task) for task in tasks], return_exceptions=True),
                    timeout=timeout
                )
            else:
                results = await asyncio.gather(*[safe_process_task(task) for task in tasks], return_exceptions=True)
            
            # Count successful results
            self.successful_tasks = sum(1 for r in results if not isinstance(r, Exception) and not str(r).startswith("Error"))
            
            # Log performance metrics
            elapsed_time = time.time() - self.start_time
            logger.info(f"Processing completed in {elapsed_time:.2f}s")
            logger.info(f"Success rate: {self.successful_tasks}/{len(tasks)} ({self.successful_tasks/len(tasks)*100:.1f}%)")
            
            return results
            
        finally:
            # Cancel rate limiter task
            rate_limiter_task.cancel()
            try:
                await rate_limiter_task
            except asyncio.CancelledError:
                pass
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if self.start_time is None:
            return {}
        
        elapsed_time = time.time() - self.start_time
        return {
            'total_tasks': self.total_tasks,
            'successful_tasks': self.successful_tasks,
            'failed_tasks': self.failed_tasks_count,
            'success_rate': self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0,
            'elapsed_time': elapsed_time,
            'tasks_per_second': self.total_tasks / elapsed_time if elapsed_time > 0 else 0,
            'max_concurrent': self.max_concurrent,
            'rate_limit_per_minute': self.rate_limit_per_minute
        }
    
    def cleanup(self):
        """Clean up resources"""
        # Cancel any remaining active tasks
        for task in self.active_tasks.values():
            if not task.done():
                task.cancel()
        
        self.active_tasks.clear()
        logger.info("Async processing manager cleaned up")


# Global processing manager instance
processing_manager = AsyncProcessingManager()