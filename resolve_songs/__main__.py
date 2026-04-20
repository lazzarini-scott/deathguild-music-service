import argparse
import asyncio
import logging

import httpx

from core.database import AsyncSessionLocal
from repository.song_repo import SongRepository
from spotify.client import SpotifyClient, SpotifyRateLimitError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 100
COOLDOWN_HOURS = 25


async def run_batch(retry: bool) -> bool:
    """Process songs until rate limited or no songs remain. Returns True if there are more songs to process."""
    resolved = 0
    not_found = 0
    total = 0

    async with httpx.AsyncClient() as http:
        spotify = SpotifyClient(http)
        await spotify.ensure_token()

        while True:
            async with AsyncSessionLocal() as session:
                repo = SongRepository(session)
                songs = await repo.get_not_found(BATCH_SIZE) if retry else await repo.get_unresolved(BATCH_SIZE)

                if not songs:
                    logger.info("No more songs to process. Resolved: %d, Not found: %d", resolved, not_found)
                    return False

                for song in songs:
                    total += 1
                    try:
                        track = await spotify.search_track(song.artist, song.title)
                    except SpotifyRateLimitError:
                        logger.warning("Rate limited after %d songs. Resolved: %d, Not found: %d", total - 1, resolved, not_found)
                        return True

                    if track:
                        await repo.set_spotify_id(song.id, track.track_id)
                        resolved += 1
                        logger.info("[%d] Resolved: %s - %s -> %s", total, song.artist, song.title, track.track_id)
                    else:
                        await repo.mark_searched(song.id)
                        not_found += 1
                        logger.info("[%d] Not found: %s - %s", total, song.artist, song.title)


async def resolve(retry: bool = False, continuous: bool = False) -> None:
    while True:
        has_more = await run_batch(retry)
        if not has_more or not continuous:
            return
        logger.info("Sleeping %d hours before next batch...", COOLDOWN_HOURS)
        await asyncio.sleep(COOLDOWN_HOURS * 3600)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve Spotify IDs for songs")
    parser.add_argument("--retry", action="store_true", help="Retry songs previously searched but not found")
    parser.add_argument("--continuous", action="store_true", help="Run until rate limited, sleep 25h, repeat")
    args = parser.parse_args()
    asyncio.run(resolve(retry=args.retry, continuous=args.continuous))


if __name__ == "__main__":
    main()
