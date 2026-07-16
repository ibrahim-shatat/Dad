"""Lightweight in-memory sliding-window rate limiter, used as a FastAPI dependency. In-process
state is fine for the single-instance free deploy; if this ever scales horizontally, swap the
backing store for Redis. Keyed by client IP (honoring X-Forwarded-For behind Render's proxy)."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

_hits: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    def __init__(self, *, limit: int, window_seconds: int, scope: str) -> None:
        self.limit = limit
        self.window = window_seconds
        self.scope = scope

    async def __call__(self, request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        key = f"{self.scope}:{_client_ip(request)}"
        now = time.monotonic()
        bucket = _hits[key]
        cutoff = now - self.window
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            retry_after = int(self.window - (now - bucket[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)
