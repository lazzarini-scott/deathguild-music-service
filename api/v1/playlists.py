import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from repository.playlist_repo import PlaylistRepository
from api.models import PlaylistSummaryResponse, PlaylistDetailResponse, PaginatedResponse, SongResponse

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get("/years", response_model=list[int])
async def list_years(session: AsyncSession = Depends(get_session)):
    repo = PlaylistRepository(session)
    return await repo.get_years()


@router.get("", response_model=PaginatedResponse)
async def list_playlists(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    year: int | None = Query(None, description="Filter by year"),
    q: str | None = Query(None, min_length=1, description="Search by date e.g. 2024-09-02"),
    session: AsyncSession = Depends(get_session),
):
    repo = PlaylistRepository(session)
    playlists, total = await repo.get_all(offset=offset, limit=limit, year=year, q=q)
    items = [
        PlaylistSummaryResponse(
            id=p.id,
            date=p.date,
            song_count=song_count,
            spotify_id=p.spotify_id,
        )
        for p, song_count in playlists
    ]
    return PaginatedResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/{playlist_date}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_date: datetime.date,
    session: AsyncSession = Depends(get_session),
):
    repo = PlaylistRepository(session)
    playlist = await repo.get_by_date(playlist_date)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    songs = await repo.get_songs_for_playlist(playlist.id)
    return PlaylistDetailResponse(
        id=playlist.id,
        date=playlist.date,
        spotify_id=playlist.spotify_id,
        songs=[
            SongResponse(
                id=song.id,
                artist=song.artist,
                title=song.title,
                position=ps.position,
                is_request=ps.is_request,
                spotify_id=song.spotify_id,
            )
            for ps, song in songs
        ],
    )
