from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from repository.song_repo import SongRepository
from api.models import PaginatedResponse, SongSearchResponse, SongPlaylistAppearance

router = APIRouter(prefix="/songs", tags=["songs"])


@router.get("", response_model=PaginatedResponse)
async def search_songs(
    q: str = Query(..., min_length=2, description="Search by artist or title"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    repo = SongRepository(session)
    songs, total = await repo.search(q=q, offset=offset, limit=limit)
    items = [
        SongSearchResponse(
            id=song.id,
            artist=song.artist,
            title=song.title,
            occurrence_count=count,
            spotify_id=song.spotify_id,
        )
        for song, count in songs
    ]
    return PaginatedResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/{song_id}/playlists", response_model=PaginatedResponse)
async def get_song_playlists(
    song_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    repo = SongRepository(session)
    appearances, total = await repo.get_playlists_for_song(
        song_id=song_id, offset=offset, limit=limit
    )
    items = [
        SongPlaylistAppearance(
            id=playlist.id,
            date=playlist.date,
            position=position,
            spotify_id=playlist.spotify_id,
        )
        for playlist, position in appearances
    ]
    return PaginatedResponse(total=total, offset=offset, limit=limit, items=items)
