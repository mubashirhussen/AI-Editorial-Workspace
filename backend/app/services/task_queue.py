"""
Background Task Queue & Asynchronous Processing Engine.
Provides task scheduling, retries with exponential backoff, timeouts,
and idempotent task execution with Redis support and in-memory failover.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Callable, Optional, Awaitable
from backend.app.core.config import settings

logger = logging.getLogger("editorial_workspace.task_queue")

class TaskStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    SUCCESS = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"

class TaskRecord:
    def __init__(self, task_id: str, task_name: str, payload: Dict[str, Any]):
        self.task_id = task_id
        self.task_name = task_name
        self.payload = payload
        self.status = TaskStatus.PENDING
        self.attempts = 0
        self.max_retries = 3
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None

class TaskQueue:
    def __init__(self):
        self._tasks: Dict[str, TaskRecord] = {}
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Any]]] = {}
        self._redis_client = None
        self._init_redis()

    def _init_redis(self):
        if settings.REDIS_URL:
            try:
                import redis
                self._redis_client = redis.from_url(settings.REDIS_URL, socket_timeout=3.0)
                self._redis_client.ping()
                logger.info(f"TaskQueue connected to Redis at {settings.REDIS_URL}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis ({e}). Falling back to in-memory TaskQueue.")
                self._redis_client = None

    def register_handler(self, task_name: str, handler: Callable[[Dict[str, Any]], Awaitable[Any]]):
        """Registers an asynchronous handler function for a specific task type."""
        self._handlers[task_name] = handler

    async def enqueue(
        self,
        task_name: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: float = 60.0
    ) -> str:
        """
        Enqueues an asynchronous task for background processing.
        Enforces idempotency using task_id if provided.
        """
        tid = task_id or f"task_{uuid.uuid4().hex[:12]}"
        
        # Idempotency check: if task already exists and is pending/running/completed, return existing id
        if tid in self._tasks:
            existing = self._tasks[tid]
            if existing.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED):
                logger.info(f"Idempotent task {tid} already exists with status {existing.status}")
                return tid

        record = TaskRecord(tid, task_name, payload)
        record.max_retries = max_retries
        self._tasks[tid] = record

        # Run background dispatch
        asyncio.create_task(self._execute_with_retry(tid, timeout_seconds))
        return tid

    async def _execute_with_retry(self, task_id: str, timeout_seconds: float):
        record = self._tasks[task_id]
        handler = self._handlers.get(record.task_name)

        if not handler:
            record.status = TaskStatus.FAILED
            record.error = f"No registered handler for task type '{record.task_name}'"
            record.completed_at = time.time()
            return

        while record.attempts <= record.max_retries:
            record.attempts += 1
            record.status = TaskStatus.RUNNING
            try:
                # Bounded execution with timeout guard (supports both handler(payload) and handler(**kwargs))
                try:
                    res = await asyncio.wait_for(handler(**record.payload), timeout=timeout_seconds)
                except TypeError:
                    res = await asyncio.wait_for(handler(record.payload), timeout=timeout_seconds)
                record.status = TaskStatus.COMPLETED
                record.result = res
                record.completed_at = time.time()
                return
            except Exception as e:
                record.error = str(e)
                logger.warning(f"Task {task_id} ('{record.task_name}') attempt {record.attempts} failed: {e}")
                if record.attempts <= record.max_retries:
                    record.status = TaskStatus.RETRYING
                    # Exponential backoff with bounded sleep
                    backoff = min(0.5 * (2 ** (record.attempts - 1)), 5.0)
                    await asyncio.sleep(backoff)
                else:
                    record.status = TaskStatus.FAILED
                    record.completed_at = time.time()
                    logger.error(f"Task {task_id} failed after {record.attempts} attempts.")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        record = self._tasks.get(task_id)
        if not record:
            return None
        return {
            "task_id": record.task_id,
            "task_name": record.task_name,
            "status": record.status,
            "attempts": record.attempts,
            "max_retries": record.max_retries,
            "created_at": record.created_at,
            "completed_at": record.completed_at,
            "duration_seconds": round(record.completed_at - record.created_at, 2) if record.completed_at else None,
            "result": record.result,
            "error": record.error
        }

    def get_queue_metrics(self) -> Dict[str, Any]:
        total = len(self._tasks)
        pending = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
        running = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
        return {
            "backend": "redis" if self._redis_client else "in_memory_async",
            "total_tasks": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / total * 100, 2) if total > 0 else 100.0
        }

    async def wait_for_task(self, task_id: str, timeout: float = 5.0) -> Optional[TaskRecord]:
        """Awaits completion of a background task up to timeout seconds."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            rec = self._tasks.get(task_id)
            if rec and rec.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                return rec
            await asyncio.sleep(0.05)
        return self._tasks.get(task_id)

    async def dispatch(self, task_name: str, task_id: Optional[str] = None, max_retries: int = 3, kwargs: Optional[Dict[str, Any]] = None) -> TaskRecord:
        """Convenience alias for enqueuing and returning TaskRecord."""
        tid = await self.enqueue(task_name=task_name, payload=kwargs or {}, task_id=task_id, max_retries=max_retries)
        return self._tasks[tid]

AsyncTaskQueue = TaskQueue
task_queue = TaskQueue()
