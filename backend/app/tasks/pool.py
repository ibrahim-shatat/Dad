from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from app.core.config import settings


async def create_arq_pool() -> ArqRedis:
    return await create_pool(RedisSettings.from_dsn(settings.redis_url))
