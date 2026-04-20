from datetime import date, datetime
from sqlalchemy import select, func, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.models import Playlist, PlaylistSong, Song


class PlaylistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_and_lock(self, playlist_id: int) -> Playlist | None:
        result = await self.session.execute(
            select(Playlist)
            .where(Playlist.id == playlist_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_date(self, playlist_date: date) -> Playlist | None:
        result = await self.session.execute(
            select(Playlist).where(Playlist.date == playlist_date)
        )
        return result.scalar_one_or_none()

    async def get_unscraped_dates(self, known_dates: list[date]) -> list[date]:
        result = await self.session.execute(
            select(Playlist.date).where(
                Playlist.date.in_(known_dates),
                Playlist.scraped_at.is_not(None)
            )
        )
        already_scraped = {row for row in result.scalars()}
        return [d for d in known_dates if d not in already_scraped]

    async def upsert(self, playlist_date: date) -> int:
        stmt = (
            pg_insert(Playlist)
            .values(date=playlist_date)
            .on_conflict_do_nothing(index_elements=["date"])
            .returning(Playlist.id)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = await self.session.scalar(
                select(Playlist.id).where(Playlist.date == playlist_date)
            )
        await self.session.commit()
        return row

    async def mark_scraped(self, playlist_id: int) -> None:
        playlist = await self.session.get(Playlist, playlist_id)
        playlist.scraped_at = datetime.utcnow()
        await self.session.commit()

    async def get_years(self) -> list[int]:
        today = date.today()
        result = await self.session.execute(
            select(func.extract("year", Playlist.date).label("year"))
            .where(Playlist.scraped_at.is_not(None), Playlist.date <= today)
            .distinct()
            .order_by("year")
        )
        return [int(row) for row in result.scalars()]

    async def get_unpushed(self, limit: int | None = None) -> list[Playlist]:
        stmt = select(Playlist).where(
                Playlist.scraped_at.is_not(None),
                Playlist.pushed_at.is_(None),
            ).order_by(Playlist.date)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def get_all(
        self, offset: int = 0, limit: int = 50, year: int | None = None, q: str | None = None
    ) -> tuple[list[tuple[Playlist, int]], int]:
        today = date.today()
        where = (Playlist.scraped_at.is_not(None)) & (Playlist.date <= today)
        if year:
            where = where & (func.extract("year", Playlist.date) == year)
        if q:
            where = where & (Playlist.date.cast(String).ilike(f"%{q}%"))
        count_result = await self.session.execute(
            select(func.count()).select_from(Playlist).where(where)
        )
        total = count_result.scalar()
        result = await self.session.execute(
            select(Playlist, func.count(PlaylistSong.id).label("song_count"))
            .outerjoin(PlaylistSong, PlaylistSong.playlist_id == Playlist.id)
            .where(where)
            .group_by(Playlist.id)
            .order_by(Playlist.date.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.tuples()), total

    async def set_spotify_id(self, playlist_id: int, spotify_id: str) -> None:
        playlist = await self.session.get(Playlist, playlist_id)
        playlist.spotify_id = spotify_id
        await self.session.commit()

    async def mark_pushed(self, playlist_id: int) -> None:
        playlist = await self.session.get(Playlist, playlist_id)
        playlist.pushed_at = datetime.utcnow()
        await self.session.commit()

    async def get_songs_for_playlist(
        self, playlist_id: int
    ) -> list[tuple[PlaylistSong, Song]]:
        result = await self.session.execute(
            select(PlaylistSong, Song)
            .join(Song, Song.id == PlaylistSong.song_id)
            .where(PlaylistSong.playlist_id == playlist_id)
            .order_by(PlaylistSong.position)
        )
        return list(result.tuples())

    async def insert_playlist_song(
        self, playlist_id: int, song_id: int, position: int, is_request: bool
    ) -> None:
        stmt = (
            pg_insert(PlaylistSong)
            .values(
                playlist_id=playlist_id,
                song_id=song_id,
                position=position,
                is_request=is_request,
            )
            .on_conflict_do_nothing()
        )
        await self.session.execute(stmt)
        await self.session.commit()


class PlaylistSongRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_spotify_track_id(
        self, playlist_song_id: int, spotify_track_id: str
    ) -> None:
        ps = await self.session.get(PlaylistSong, playlist_song_id)
        ps.spotify_track_id = spotify_track_id
        await self.session.commit()
