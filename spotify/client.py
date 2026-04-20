import asyncio
import logging
import re
import unicodedata
from dataclasses import dataclass

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception, wait_fixed

from core.config import settings

logger = logging.getLogger(__name__)

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


def _normalize(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()


def _compact(text: str) -> str:
    """Strip everything except alphanumeric chars for loose comparison."""
    text = _normalize(text)
    text = text.replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", text)


def _strip_parentheticals(text: str) -> str:
    """Remove trailing parenthetical suffixes like (Remix), (Featuring X)."""
    return re.sub(r"\s*\(.*\)\s*$", "", text).strip()


def _artist_match(our_artist: str, spotify_artists: list[str]) -> bool:
    ours = _normalize(our_artist)
    ours_compact = _compact(our_artist)
    for sa in spotify_artists:
        theirs = _normalize(sa)
        theirs_compact = _compact(sa)
        if ours == theirs or ours in theirs or theirs in ours:
            return True
        if ours_compact == theirs_compact or ours_compact in theirs_compact or theirs_compact in ours_compact:
            return True
    combined = _normalize(", ".join(spotify_artists))
    combined_compact = _compact(", ".join(spotify_artists))
    return ours in combined or combined in ours or ours_compact in combined_compact or combined_compact in ours_compact


def _title_match(our_title: str, spotify_title: str) -> bool:
    ours = _normalize(our_title)
    theirs = _normalize(spotify_title)
    if ours == theirs:
        return True
    ours_stripped = _normalize(_strip_parentheticals(our_title))
    theirs_stripped = _normalize(_strip_parentheticals(spotify_title))
    if ours_stripped == theirs_stripped:
        return True
    if ours_stripped.startswith(theirs_stripped) or theirs_stripped.startswith(ours_stripped):
        return True
    # Compact comparison: ignore hyphens, spaces, punctuation
    ours_compact = _compact(_strip_parentheticals(our_title))
    theirs_compact = _compact(_strip_parentheticals(spotify_title))
    if ours_compact == theirs_compact:
        return True
    if ours_compact.startswith(theirs_compact) or theirs_compact.startswith(ours_compact):
        return True
    if _fuzzy_close(ours_compact, theirs_compact):
        return True
    return False


def _fuzzy_close(a: str, b: str, threshold: float = 0.85) -> bool:
    """Check if two strings are similar enough by character overlap ratio."""
    if not a or not b:
        return False
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) / len(longer) < threshold:
        return False
    matches = sum(1 for c in shorter if c in longer)
    return matches / len(longer) >= threshold


class SpotifyRateLimitError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


@dataclass
class SpotifyTrack:
    track_id: str
    name: str
    artist: str


class SpotifyClient:
    def __init__(self, client: httpx.AsyncClient, request_delay: float = 2.0):
        self._client = client
        self._access_token: str | None = None
        self._request_delay = request_delay

    async def ensure_token(self) -> None:
        response = await self._client.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": settings.spotify_refresh_token,
            },
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
        )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _get(self, url: str, **kwargs) -> dict:
        await asyncio.sleep(self._request_delay)
        response = await self._client.get(url, headers=self._headers(), **kwargs)
        if response.status_code == 429:
            raw = response.headers.get("Retry-After", "5")
            retry_after = min(int(raw), 120)
            logger.warning("Rate limited (Retry-After raw=%s, using %ds)", raw, retry_after)
            await asyncio.sleep(retry_after)
            raise SpotifyRateLimitError(retry_after)
        if response.status_code == 401:
            await self.ensure_token()
            raise SpotifyRateLimitError(0)
        response.raise_for_status()
        return response.json()

    async def _post(self, url: str, **kwargs) -> dict:
        response = await self._client.post(url, headers=self._headers(), **kwargs)
        if response.status_code == 429:
            raw = response.headers.get("Retry-After", "5")
            retry_after = min(int(raw), 120)
            logger.warning("Rate limited (Retry-After raw=%s, using %ds)", raw, retry_after)
            await asyncio.sleep(retry_after)
            raise SpotifyRateLimitError(retry_after)
        if response.status_code == 401:
            await self.ensure_token()
            raise SpotifyRateLimitError(0)
        response.raise_for_status()
        return response.json()

    @retry(
        retry=retry_if_exception(lambda e: isinstance(e, SpotifyRateLimitError)),
        wait=wait_fixed(1),
        stop=stop_after_attempt(10),
    )
    async def search_track(self, artist: str, title: str) -> SpotifyTrack | None:
        clean_title = _strip_parentheticals(title)
        # Tier 1: structured search with artist + title matching
        params = {"q": f"artist:{artist} track:{clean_title}", "type": "track", "limit": 10}
        data = await self._get(f"{API_BASE}/search", params=params)
        items = data.get("tracks", {}).get("items", [])
        for item in items:
            item_artists = [a["name"] for a in item["artists"]]
            if _artist_match(artist, item_artists) and _title_match(title, item["name"]):
                return SpotifyTrack(
                    track_id=item["id"],
                    name=item["name"],
                    artist=item["artists"][0]["name"],
                )
        # Tier 2: plain text search with artist + title matching, then top-result title-only fallback
        params = {"q": f"{artist} {clean_title}", "type": "track", "limit": 10}
        data = await self._get(f"{API_BASE}/search", params=params)
        items = data.get("tracks", {}).get("items", [])
        for item in items:
            item_artists = [a["name"] for a in item["artists"]]
            if _artist_match(artist, item_artists) and _title_match(title, item["name"]):
                return SpotifyTrack(
                    track_id=item["id"],
                    name=item["name"],
                    artist=item["artists"][0]["name"],
                )
        # Tier 3: trust Spotify's top result if title matches (handles abbreviations like OMD)
        if items and _title_match(title, items[0]["name"]):
            item = items[0]
            return SpotifyTrack(
                track_id=item["id"],
                name=item["name"],
                artist=item["artists"][0]["name"],
            )
        return None

    @retry(
        retry=retry_if_exception(lambda e: isinstance(e, SpotifyRateLimitError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
    )
    async def get_current_user_id(self) -> str:
        data = await self._get(f"{API_BASE}/me")
        return data["id"]

    @retry(
        retry=retry_if_exception(lambda e: isinstance(e, SpotifyRateLimitError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
    )
    async def create_playlist(self, name: str) -> str:
        data = await self._post(
            f"{API_BASE}/me/playlists",
            json={"name": name, "public": True},
        )
        return data["id"]

    @retry(
        retry=retry_if_exception(lambda e: isinstance(e, SpotifyRateLimitError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
    )
    async def add_tracks(self, playlist_id: str, track_ids: list[str]) -> None:
        uris = [f"spotify:track:{tid}" for tid in track_ids]
        for i in range(0, len(uris), 100):
            await self._post(
                f"{API_BASE}/playlists/{playlist_id}/items",
                json={"uris": uris[i:i + 100]},
            )
