import uuid
from abc import ABC, abstractmethod
from pathlib import Path

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


def get_storage_backend() -> StorageBackend:
    if settings.storage_backend == "local":
        return LocalStorageBackend()
    raise ValueError(f"Unknown storage backend: {settings.storage_backend}")
