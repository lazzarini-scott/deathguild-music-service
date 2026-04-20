import asyncio
import logging
from datetime import date

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from repository.playlist_repo import PlaylistRepository
from repository.song_repo import SongRepository
from scraper.parser import ParsedPlaylist, parse_playlist, parse_playlist_urls

logger = logging.getLogger(__name__)

MAX_CONCURRENCY = 1
TIMEOUT = 30


class ScraperClient:
    def __init__(self, session: AsyncSession):
        self.playlist_repo = PlaylistRepository(session)
        self.song_repo = SongRepository(session)
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async def run(self):
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            index_html = await self._fetch(client, f"{settings.deathguild_base_url}/playdates/")
            if not index_html:
                logger.error("Failed to fetch index page, aborting.")
                return

            all_urls = parse_playlist_urls(index_html)
            logger.info(f"Found {len(all_urls)} playlist URLs")

            all_dates = _extract_dates(all_urls)
            urls_to_scrape = await self._filter_unscraped(all_urls, all_dates)
            logger.info(f"{len(urls_to_scrape)} playlists need scraping")

            tasks = [self._scrape_and_store(client, url) for url in urls_to_scrape]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _filter_unscraped(self, urls: list[str], all_dates: list[date]) -> list[str]:
        unscraped_dates = set(await self.playlist_repo.get_unscraped_dates(all_dates))
        return [url for url, d in zip(urls, all_dates) if d in unscraped_dates]

    async def _scrape_and_store(self, client: httpx.AsyncClient, url: str):
        async with self._semaphore:
            html = await self._fetch(client, url)
            if not html:
                return

            parsed = parse_playlist(html, url)
            if not parsed:
                return

            await self._store(parsed)

    async def _store(self, parsed: ParsedPlaylist):
        playlist_id = await self.playlist_repo.upsert(parsed.date)
        for song in parsed.songs:
            song_id = await self.song_repo.upsert(song.artist, song.title)
            await self.playlist_repo.insert_playlist_song(
                playlist_id, song_id, song.position, song.is_request
            )
        await self.playlist_repo.mark_scraped(playlist_id)
        logger.info(f"Stored playlist {parsed.date} with {len(parsed.songs)} songs")

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> str | None:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {url}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
        return None


def _extract_dates(urls: list[str]) -> list[date]:
    from datetime import date as date_type
    dates = []
    for url in urls:
        segment = url.rstrip("/").split("/")[-1]
        try:
            dates.append(date_type.fromisoformat(segment))
        except ValueError:
            logger.warning(f"Could not extract date from URL: {url}")
            dates.append(None)
    return dates
