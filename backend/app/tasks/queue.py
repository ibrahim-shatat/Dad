"""Job dispatch abstraction so the same endpoint code works with either backend:

- ``arq`` (default, local/VM): jobs are enqueued to Redis and run by the arq worker.
- ``inline`` (free/serverless deploy with no worker): jobs run in-process as FastAPI
  background tasks, so no Redis or separate worker process is required.

Selected via the ``JOB_MODE`` env var / ``settings.job_mode``.
"""

from typing import Any

from fastapi import BackgroundTasks, Request

from app.core.config import settings


class _InlineRedis:
    """Stands in for arq's ``ctx['redis']`` so a job that chains to another job
    (``ctx['redis'].enqueue_job(...)``) runs that next job inline as well."""

    async def enqueue_job(self, name: str, *args: Any, **kwargs: Any) -> None:
        await run_job_inline(name, *args)


_INLINE_CTX: dict[str, Any] = {"redis": _InlineRedis()}


async def run_job_inline(name: str, *args: Any) -> None:
    # Imported lazily to avoid a circular import (jobs -> services -> ... at module load).
    from app.tasks import jobs

    func = getattr(jobs, name)
    await func(_INLINE_CTX, *args)


class JobEnqueuer:
    """Uniform ``enqueue_job`` interface used by endpoints, backed by either arq or
    in-process background tasks depending on ``settings.job_mode``."""

    def __init__(self, pool: Any | None, background_tasks: BackgroundTasks) -> None:
        self._pool = pool
        self._background_tasks = background_tasks

    async def enqueue_job(self, name: str, *args: Any) -> None:
        if settings.job_mode == "inline":
            self._background_tasks.add_task(run_job_inline, name, *args)
        else:
            await self._pool.enqueue_job(name, *args)


async def get_job_queue(request: Request, background_tasks: BackgroundTasks) -> JobEnqueuer:
    pool = getattr(request.app.state, "arq_pool", None)
    return JobEnqueuer(pool, background_tasks)
