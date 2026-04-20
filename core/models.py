import datetime
from typing import Optional
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Song(SQLModel, table=True):
    __tablename__ = "songs"
    __table_args__ = (UniqueConstraint("artist", "title", name="uq_song_artist_title"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    artist: str
    spotify_id: Optional[str] = None
    spotify_searched_at: Optional[datetime.datetime] = None


class Playlist(SQLModel, table=True):
    __tablename__ = "playlists"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime.date = Field(unique=True, index=True)
    spotify_id: Optional[str] = None
    scraped_at: Optional[datetime.datetime] = None
    pushed_at: Optional[datetime.datetime] = None


class PlaylistSong(SQLModel, table=True):
    __tablename__ = "playlist_songs"
    __table_args__ = (UniqueConstraint("playlist_id", "song_id", name="uq_playlist_song"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlists.id")
    song_id: int = Field(foreign_key="songs.id")
    position: int
    is_request: bool = False
    spotify_track_id: Optional[str] = None
