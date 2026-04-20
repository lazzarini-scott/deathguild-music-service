import logging
import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "http://www.deathguild.com"


@dataclass
class ParsedSong:
    artist: str
    title: str
    position: int
    is_request: bool


@dataclass
class ParsedPlaylist:
    date: date
    songs: list[ParsedSong]


def parse_playlist_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all(
        "a", href=lambda x: x and re.fullmatch(r"/playlist/\d{4}-\d{2}-\d{2}", x)
    )
    return [urljoin(BASE_URL, link["href"]) for link in links]


def parse_playlist(html: str, url: str) -> ParsedPlaylist | None:
    try:
        soup = BeautifulSoup(html, "html.parser")

        date_span = soup.find("span", class_="date")
        if not date_span:
            raise ValueError("Missing date span")
        playlist_date = date.fromisoformat(
            __parse_date_text(date_span.get_text(strip=True))
        )

        songs = []
        for position, song_tag in enumerate(soup.find_all("em"), start=1):
            parsed = _parse_song(song_tag, position)
            if parsed:
                songs.append(parsed)

        return ParsedPlaylist(date=playlist_date, songs=songs)
    except Exception as e:
        logger.error(f"Failed to parse playlist from {url}: {e}")
        return None


def _parse_song(song_tag, position: int) -> ParsedSong | None:
    try:
        artist = song_tag.get_text(strip=True)
        if not artist:
            return None

        sibling = song_tag.next_sibling
        if not sibling or "-" not in sibling:
            return None
        title = sibling.replace("-", "", 1).strip()
        if not title:
            return None

        is_request = False
        request_tag = song_tag.find_next_sibling()
        if request_tag and "request" in request_tag.get("class", []):
            is_request = True

        return ParsedSong(artist=artist, title=title, position=position, is_request=is_request)
    except Exception as e:
        logger.warning(f"Skipping malformed song entry at position {position}: {e}")
        return None


def __parse_date_text(date_text: str) -> str:
    from datetime import datetime
    return datetime.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")
