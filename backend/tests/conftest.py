import os

# Must happen before any `app.*` import — pydantic-settings reads env vars once, at import
# time, so redirecting DATABASE_URL later (e.g. via monkeypatch) would be too late.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://dad:dad@db:5432/dad_test")

import asyncio  # noqa: E402
import sys  # noqa: E402
import uuid  # noqa: E402
from collections.abc import AsyncGenerator  # noqa: E402
from pathlib import Path  # noqa: E402

# On Windows, asyncpg + the default ProactorEventLoop crashes during connection teardown
# ("'NoneType' object has no attribute 'send'") when the test loop closes. The SelectorEventLoop
# avoids it. No effect on Linux/CI (where the app actually runs).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.config import settings  # noqa: E402

_TABLES_TO_TRUNCATE = [
    "email_drafts",
    "email_messages",
    "email_accounts",
    "decisions",
    "action_items",
    "meetings",
    "presentations",
    "document_reviews",
    "documents",
    "approval_queue_items",
    "users",
]


def _require_test_database() -> None:
    db_name = settings.database_url.rsplit("/", 1)[-1]
    if not db_name.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run tests against non-test database {db_name!r}. Set DATABASE_URL "
            "to a '*_test' database before running pytest (see backend/tests/conftest.py)."
        )


_require_test_database()


async def _ensure_database_exists() -> None:
    db_name = settings.database_url.rsplit("/", 1)[-1]
    admin_url = settings.database_url.rsplit("/", 1)[0] + "/postgres"
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_test_database():
    await _ensure_database_exists()

    from alembic import command
    from alembic.config import Config

    cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    await asyncio.to_thread(command.upgrade, cfg, "head")
    yield


@pytest_asyncio.fixture(autouse=True)
async def _clean_db():
    yield

    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        for table in _TABLES_TO_TRUNCATE:
            await session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
        await session.commit()


@pytest_asyncio.fixture
async def db_session():
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        yield session


class FakeArqPool:
    """Stands in for the real arq Redis pool in tests — records enqueue calls instead of
    touching Redis. Feature jobs are invoked directly in tests rather than via a real worker
    (see tests/test_*_flow.py), so nothing needs to actually process this queue.
    """

    def __init__(self) -> None:
        self.enqueued: list[tuple[str, tuple, dict]] = []

    async def enqueue_job(self, function: str, *args, **kwargs):
        self.enqueued.append((function, args, kwargs))
        return None


@pytest_asyncio.fixture
async def arq_pool_fake() -> FakeArqPool:
    return FakeArqPool()


@pytest_asyncio.fixture
async def client(arq_pool_fake: FakeArqPool) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    from app.tasks.queue import get_job_queue

    # Endpoints enqueue via the JobEnqueuer dependency; swap it for a fake that records
    # enqueue calls instead of touching Redis or running jobs in-process.
    app.dependency_overrides[get_job_queue] = lambda: arq_pool_fake

    # https:// (not http://) so httpx's cookie jar will actually store/resend the refresh
    # cookie, which the app sets with Secure=True — ASGITransport never touches real TLS
    # either way, this only affects httpx's own cookie-scheme bookkeeping.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def make_user(db_session):
    from app.core.security import hash_password
    from app.models.user import User, UserRole

    async def _make_user(
        email: str | None = None,
        role: UserRole = UserRole.director,
        password: str = "testpass123",
    ):
        user = User(
            email=email or f"{uuid.uuid4().hex[:12]}@example.com",
            hashed_password=hash_password(password),
            full_name="Test User",
            role=role,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user, attribute_names=["created_at"])
        return user

    return _make_user


@pytest_asyncio.fixture
async def auth_user(make_user):
    """A director user + matching auth headers — the common case for endpoint tests."""
    from app.core.security import create_access_token

    user = await make_user()
    token = create_access_token(user.id)
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fake_ctx(arq_pool_fake: FakeArqPool) -> dict:
    """A minimal arq `ctx` dict for calling job functions directly (bypassing a real worker)."""
    return {"redis": arq_pool_fake}


@pytest.fixture
def mock_claude(monkeypatch):
    """Patches claude_client.structured_call so tests never hit the real Anthropic API.
    Configure per-test with `mock_claude.return_value = ...` or `.side_effect = ...`.
    """
    from unittest.mock import AsyncMock

    from app.services.ai.client import claude_client

    mock = AsyncMock()
    monkeypatch.setattr(claude_client, "structured_call", mock)
    return mock
