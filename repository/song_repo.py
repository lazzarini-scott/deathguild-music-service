from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.models import Song, Playlist, PlaylistSong


class SongRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_artist_and_title(self, artist: str, title: str) -> Song | None:
        result = await self.session.execute(
            select(Song).where(Song.artist == artist, Song.title == title)
        )
        return result.scalar_one_or_none()

    async def upsert(self, artist: str, title: str) -> int:
        stmt = (
            pg_insert(Song)
            .values(artist=artist, title=title)
            .on_conflict_do_nothing(index_elements=["artist", "title"])
            .returning(Song.id)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = await self.session.scalar(
                select(Song.id).where(Song.artist == artist, Song.title == title)
            )
        await self.session.commit()
        return row

    async def set_spotify_id(self, song_id: int, spotify_id: str) -> None:
        song = await self.session.get(Song, song_id)
        song.spotify_id = spotify_id
        song.spotify_searched_at = datetime.utcnow()
        await self.session.commit()

    async def mark_searched(self, song_id: int) -> None:
        song = await self.session.get(Song, song_id)
        song.spotify_searched_at = datetime.utcnow()
        await self.session.commit()

    async def get_unresolved(self, limit: int = 100) -> list[Song]:
        result = await self.session.execute(
            select(Song)
            .where(Song.spotify_id.is_(None), Song.spotify_searched_at.is_(None))
            .order_by(Song.id)
            .limit(limit)
        )
        return list(result.scalars())

    async def get_not_found(self, limit: int = 100) -> list[Song]:
        result = await self.session.execute(
            select(Song)
            .where(Song.spotify_id.is_(None), Song.spotify_searched_at.is_not(None))
            .order_by(Song.id)
            .limit(limit)
        )
        return list(result.scalars())

    async def search(self, q: str, offset: int = 0, limit: int = 50) -> tuple[list[tuple[Song, int]], int]:
        pattern = f"%{q}%"
        where = (Song.artist.ilike(pattern)) | (Song.title.ilike(pattern))
        count_result = await self.session.execute(
            select(func.count()).select_from(Song).where(where)
        )
        total = count_result.scalar()
        result = await self.session.execute(
            select(Song, func.count(PlaylistSong.id).label("occurrence_count"))
            .outerjoin(PlaylistSong, PlaylistSong.song_id == Song.id)
            .where(where)
            .group_by(Song.id)
            .order_by(func.count(PlaylistSong.id).desc(), Song.artist, Song.title)
            .offset(offset)
            .limit(limit)
        )
        return list(result.tuples()), total

    async def get_playlists_for_song(
        self, song_id: int, offset: int = 0, limit: int = 50
    ) -> tuple[list[tuple[Playlist, int]], int]:
        where = PlaylistSong.song_id == song_id
        count_result = await self.session.execute(
            select(func.count()).select_from(PlaylistSong).where(where)
        )
        total = count_result.scalar()
        result = await self.session.execute(
            select(Playlist, PlaylistSong.position)
            .join(PlaylistSong, PlaylistSong.playlist_id == Playlist.id)
            .where(where)
            .order_by(Playlist.date.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.tuples()), total
