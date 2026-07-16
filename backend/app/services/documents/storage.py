import mimetypes
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, data: bytes, filename: str) -> str:
        """Persist `data` and return a storage key that `read`/`delete` can use later."""

    @abstractmethod
    async def read(self, key: str) -> bytes:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str | None = None) -> None:
        self._base_dir = Path(base_dir or settings.upload_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        return self._base_dir / key

    async def save(self, data: bytes, filename: str) -> str:
        suffix = Path(filename).suffix
        key = f"{uuid.uuid4()}{suffix}"
        self._resolve(key).write_bytes(data)
        return key

    async def read(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()


class SupabaseStorageBackend(StorageBackend):
    """Durable object storage via Supabase Storage's REST API. Uses the service-role key, so it
    stays entirely server-side and works with a private bucket."""

    def __init__(self) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError(
                "storage_backend=supabase requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
            )
        self._object_base = settings.supabase_url.rstrip("/") + "/storage/v1/object"
        self._bucket = settings.supabase_storage_bucket
        self._auth = {"Authorization": f"Bearer {settings.supabase_service_role_key}"}

    def _url(self, key: str) -> str:
        return f"{self._object_base}/{self._bucket}/{key}"

    async def save(self, data: bytes, filename: str) -> str:
        key = f"{uuid.uuid4()}{Path(filename).suffix}"
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                self._url(key),
                content=data,
                headers={**self._auth, "Content-Type": content_type, "x-upsert": "true"},
            )
            resp.raise_for_status()
        return key

    async def read(self, key: str) -> bytes:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(self._url(key), headers=self._auth)
            resp.raise_for_status()
            return resp.content

    async def delete(self, key: str) -> None:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.delete(self._url(key), headers=self._auth)
            if resp.status_code not in (200, 404):
                resp.raise_for_status()


def get_storage_backend() -> StorageBackend:
    if settings.storage_backend == "local":
        return LocalStorageBackend()
    if settings.storage_backend == "supabase":
        return SupabaseStorageBackend()
    raise ValueError(f"Unknown storage backend: {settings.storage_backend}")
