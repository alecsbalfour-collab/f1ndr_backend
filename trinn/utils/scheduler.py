# f1ndr-backend/trinn/utils/scheduler.py
"""
DICT-aligned TRINN scheduler with enterprise features.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import uuid

from trinn.db.trinn_repo import tasks_store

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Enterprise scheduled task with DICT patterns."""
    task_id: str
    task_data: Dict[str, Any]
    interval_hours: int
    next_run: datetime
    created_at: datetime
    last_run: Optional[datetime] = None
    run_count: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerMetrics:
    """Enterprise scheduler metrics for monitoring."""
    total_scheduled_tasks: int = 0
    active_tasks: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    average_run_time_ms: float = 0.0


class TrinnScheduler:
    """Enterprise TRINN scheduler with DICT patterns."""
    
    def __init__(self):
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.worker_tasks: list = []
        self.metrics = SchedulerMetrics()
        self._lock = asyncio.Lock()
        
        logger.info("TrinnScheduler initialized")
    
    async def start(self, num_workers: int = 3) -> None:
        """Start the scheduler with worker tasks."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        logger.info(f"Starting scheduler with {num_workers} workers")
        
        # Start worker tasks
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker)
        
        # Start scheduler task
        scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.worker_tasks.append(scheduler_task)
        
        logger.info("Scheduler started successfully")
    
    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if not self.running:
            logger.warning("Scheduler not running")
            return
        
        logger.info("Stopping scheduler...")
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("Scheduler stopped")
    
    async def schedule_interval(
        self,
        task_data: Dict[str, Any],
        interval_hours: int,
        task_id: Optional[str] = None,
        next_run: Optional[datetime] = None,
        last_run: Optional[datetime] = None,
        run_count: int = 0,
        last_error: Optional[str] = None,
    ) -> str:
        """
        Schedule a task to run at regular intervals.

        Args:
            task_data: Task data to execute
            interval_hours: Interval between runs in hours
            task_id: Optional task ID (will be generated if not provided)
            next_run: Optional first run time (defaults to now + interval)
            last_run, run_count, last_error: Prior run state when restoring a persisted task

        Returns:
            Task ID of the scheduled task
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        async with self._lock:
            next_run = next_run or datetime.utcnow() + timedelta(hours=interval_hours)

            scheduled_task = ScheduledTask(
                task_id=task_id,
                task_data=task_data,
                interval_hours=interval_hours,
                next_run=next_run,
                created_at=datetime.utcnow(),
                last_run=last_run,
                run_count=run_count,
                metadata={"last_error": last_error},
            )

            # Re-scheduling an existing ID replaces it; only count genuinely new tasks.
            existing = self.scheduled_tasks.get(task_id)
            if existing is None:
                self.metrics.total_scheduled_tasks += 1
            elif existing.enabled:
                existing.enabled = False  # a queued copy of the old version must not run
                self.metrics.active_tasks -= 1
            self.scheduled_tasks[task_id] = scheduled_task
            self.metrics.active_tasks += 1
            
            logger.info(f"Scheduled task {task_id} to run at {next_run}")
            return task_id
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if task was cancelled
        """
        async with self._lock:
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id].enabled = False
                self.metrics.active_tasks -= 1
                logger.info(f"Cancelled task {task_id}")
                return True
            return False
    
    @staticmethod
    def _task_snapshot(task: ScheduledTask) -> Dict[str, Any]:
        return {
            "task_id": task.task_id,
            "task": task.task_data.get("task"),
            "task_data": task.task_data,
            "enabled": task.enabled,
            "next_run": task.next_run.isoformat(),
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "run_count": task.run_count,
            "last_error": task.metadata.get("last_error"),
            "interval_hours": task.interval_hours,
            "created_at": task.created_at.isoformat(),
        }

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a scheduled task.

        Args:
            task_id: Task ID to query

        Returns:
            Task status dictionary or None if not found
        """
        async with self._lock:
            task = self.scheduled_tasks.get(task_id)
            return self._task_snapshot(task) if task else None

    async def list_tasks(self) -> list:
        """Snapshot of every scheduled task, enabled or not."""
        async with self._lock:
            return [self._task_snapshot(task) for task in self.scheduled_tasks.values()]

    async def remove_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task entirely (disable + drop from the table).

        Returns:
            True if the task existed
        """
        async with self._lock:
            task = self.scheduled_tasks.pop(task_id, None)
            if task is None:
                return False
            if task.enabled:
                task.enabled = False  # workers skip a copy that's already queued
                self.metrics.active_tasks -= 1
            logger.info(f"Removed task {task_id}")
            return True
    
    async def _queue_due_tasks(self) -> int:
        """Queue every enabled task whose next_run has passed; returns how many."""
        now = datetime.utcnow()
        due_tasks = []
        async with self._lock:
            for task in self.scheduled_tasks.values():
                if task.enabled and task.next_run <= now:
                    # Claim the slot now: a run longer than one tick must not
                    # be queued again (and run concurrently on another worker).
                    task.next_run = now + timedelta(hours=task.interval_hours)
                    due_tasks.append(task)
        for task in due_tasks:
            await self.task_queue.put(task)
            logger.debug(f"Queued task {task.task_id} for execution")
        return len(due_tasks)

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop to check for due tasks."""
        while self.running:
            try:
                await self._queue_due_tasks()

                # Sleep for a short interval before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _worker(self, worker_name: str) -> None:
        """Worker task to execute queued tasks."""
        logger.info(f"Worker {worker_name} started")
        
        while self.running:
            try:
                # Wait for task with timeout
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    continue
                
                if not task.enabled:
                    self.task_queue.task_done()
                    continue
                
                logger.info(f"Worker {worker_name} executing task {task.task_id}")
                
                # Execute task
                start_time = datetime.utcnow()
                try:
                    await self._execute_task(task)
                    
                    # Update metrics
                    run_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                    self.metrics.completed_runs += 1
                    self._update_average_run_time(run_time)
                    
                    logger.info(f"Task {task.task_id} completed in {run_time:.2f}ms")
                    
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    self.metrics.failed_runs += 1
                
                finally:
                    self.task_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a scheduled task and reschedule if needed."""
        # Import here to avoid circular dependency
        from trinn.core.core import run_task

        try:
            task.metadata["last_result"] = await run_task(task.task_data)
            task.metadata["last_error"] = None
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.metadata["last_error"] = str(e)
            raise
        finally:
            async with self._lock:
                task.last_run = datetime.utcnow()
                task.run_count += 1
                # A failed run still consumed its slot: push next_run out by the
                # interval so a failing task doesn't retry on every scheduler tick.
                if task.enabled:
                    task.next_run = datetime.utcnow() + timedelta(hours=task.interval_hours)
            await self._persist_run_state(task)

    @staticmethod
    async def _persist_run_state(task: ScheduledTask) -> None:
        """Save run state so a restart resumes the schedule instead of firing every task at boot."""
        try:
            await tasks_store.update(task.task_id, {
                "next_run": task.next_run.isoformat(),
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "run_count": task.run_count,
                "last_error": task.metadata.get("last_error"),
                "updated_at": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning(f"Could not persist run state for task {task.task_id}: {e}")
    
    def _update_average_run_time(self, new_time: float) -> None:
        """Update average run time with exponential smoothing."""
        alpha = 0.1  # Smoothing factor
        if self.metrics.average_run_time_ms == 0:
            self.metrics.average_run_time_ms = new_time
        else:
            self.metrics.average_run_time_ms = (
                alpha * new_time + (1 - alpha) * self.metrics.average_run_time_ms
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler metrics for monitoring."""
        return {
            "total_scheduled_tasks": self.metrics.total_scheduled_tasks,
            "active_tasks": self.metrics.active_tasks,
            "completed_runs": self.metrics.completed_runs,
            "failed_runs": self.metrics.failed_runs,
            "average_run_time_ms": self.metrics.average_run_time_ms,
            "success_rate": self._calculate_success_rate(),
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.metrics.completed_runs + self.metrics.failed_runs
        if total == 0:
            return 0.0
        return (self.metrics.completed_runs / total) * 100


# Global scheduler instance
_scheduler: Optional[TrinnScheduler] = None


def get_scheduler() -> TrinnScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TrinnScheduler()
    return _scheduler


def get_scheduler_state() -> Dict[str, Any]:
    """Scheduler status for readiness checks, without creating the scheduler."""
    if _scheduler is None:
        return {"status": "not_started"}
    if not _scheduler.running:
        return {"status": "stopped", **_scheduler.get_metrics()}
    dead = sum(1 for task in _scheduler.worker_tasks if task.done())
    return {
        "status": "failed" if dead else "running",
        "dead_tasks": dead,
        **_scheduler.get_metrics(),
    }


async def stop_scheduler() -> None:
    """Stop the global scheduler if it was ever started (no-op otherwise)."""
    if _scheduler is not None and _scheduler.running:
        await _scheduler.stop()


# Legacy function for backward compatibility
def schedule_interval(task: Dict[str, Any], hours: int) -> bool:
    """Legacy function to schedule task (deprecated, use TrinnScheduler directly)."""
    logger.warning("schedule_interval is deprecated, use TrinnScheduler.schedule_interval instead")
    
    scheduler = get_scheduler()
    
    # For backward compatibility, this is a synchronous wrapper
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(scheduler.schedule_interval(task, hours))
        return True
    except Exception as e:
        logger.error(f"Failed to schedule task: {e}")
        return False
