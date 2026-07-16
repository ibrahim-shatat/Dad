import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.tasks.pool import create_arq_pool

# How often the in-process scheduler re-syncs every connected account (inline mode only).
_AUTO_SYNC_INTERVAL_SECONDS = 3600


async def _auto_sync_loop() -> None:
    """Inline-mode background scheduler: periodically re-sync email + calendar for all accounts.

    In arq mode this is handled by the worker's cron jobs instead. On free hosting the web
    service may sleep when idle, pausing this loop; it resumes on the next request, and the manual
    "Sync" buttons always work regardless.
    """
    from app.tasks.jobs import sync_all_calendars, sync_all_email_accounts
    from app.tasks.queue import _INLINE_CTX

    while True:
        await asyncio.sleep(_AUTO_SYNC_INTERVAL_SECONDS)
        try:
            await sync_all_email_accounts(_INLINE_CTX)
            await sync_all_calendars(_INLINE_CTX)
        except Exception:
            # Never let a transient sync failure kill the scheduler.
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # In "inline" mode there is no Redis/worker — jobs run in-process — so skip the pool and run
    # the periodic sync in-process instead.
    app.state.arq_pool = await create_arq_pool() if settings.job_mode == "arq" else None
    sync_task = (
        asyncio.create_task(_auto_sync_loop()) if settings.job_mode == "inline" else None
    )
    yield
    if sync_task is not None:
        sync_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sync_task
    if app.state.arq_pool is not None:
        await app.state.arq_pool.close()


app = FastAPI(title="Dad — AI Executive Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
