import datetime
from typing import Optional
from urllib.parse import quote_plus
from pydantic import BaseModel, computed_field


class SongResponse(BaseModel):
    id: int
    artist: str
    title: str
    position: int
    is_request: bool
    spotify_id: Optional[str] = None

    @computed_field
    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/results?search_query={quote_plus(f'{self.artist} {self.title}')}"

    @computed_field
    @property
    def spotify_url(self) -> Optional[str]:
        if self.spotify_id:
            return f"https://open.spotify.com/track/{self.spotify_id}"
        return None


class SongSearchResponse(BaseModel):
    id: int
    artist: str
    title: str
    occurrence_count: int
    spotify_id: Optional[str] = None

    @computed_field
    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/results?search_query={quote_plus(f'{self.artist} {self.title}')}"

    @computed_field
    @property
    def spotify_url(self) -> Optional[str]:
        if self.spotify_id:
            return f"https://open.spotify.com/track/{self.spotify_id}"
        return None


class SongPlaylistAppearance(BaseModel):
    id: int
    date: datetime.date
    position: int
    spotify_id: Optional[str] = None

    @computed_field
    @property
    def spotify_url(self) -> Optional[str]:
        if self.spotify_id:
            return f"https://open.spotify.com/playlist/{self.spotify_id}"
        return None


class PlaylistSummaryResponse(BaseModel):
    id: int
    date: datetime.date
    song_count: int
    spotify_id: Optional[str] = None

    @computed_field
    @property
    def spotify_url(self) -> Optional[str]:
        if self.spotify_id:
            return f"https://open.spotify.com/playlist/{self.spotify_id}"
        return None


class PlaylistDetailResponse(BaseModel):
    id: int
    date: datetime.date
    spotify_id: Optional[str] = None
    songs: list[SongResponse]

    @computed_field
    @property
    def spotify_url(self) -> Optional[str]:
        if self.spotify_id:
            return f"https://open.spotify.com/playlist/{self.spotify_id}"
        return None


class PaginatedResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: list
