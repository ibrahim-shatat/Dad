from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.tasks.pool import create_arq_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # In "inline" mode there is no Redis/worker — jobs run in-process — so skip the pool.
    app.state.arq_pool = await create_arq_pool() if settings.job_mode == "arq" else None
    yield
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
