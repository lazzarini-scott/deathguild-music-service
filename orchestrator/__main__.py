import asyncio
import logging

from arq.connections import create_pool, RedisSettings

from core.config import settings
from core.database import AsyncSessionLocal
from repository.playlist_repo import PlaylistRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    async with AsyncSessionLocal() as session:
        repo = PlaylistRepository(session)
        unpushed = await repo.get_unpushed(limit=5)

    if not unpushed:
        logger.info("No unpushed playlists found")
        return

    logger.info(f"Enqueueing {len(unpushed)} playlists to push to Spotify")
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    for playlist in unpushed:
        await redis.enqueue_job("push_playlist", playlist.id, _job_id=f"push_playlist_{playlist.id}")
        logger.info(f"Enqueued playlist {playlist.date} (id=push_playlist_{playlist.id})")
    await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
