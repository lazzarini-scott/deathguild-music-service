import logging

import httpx
from arq.connections import RedisSettings

from core.config import settings
from core.database import AsyncSessionLocal
from repository.playlist_repo import PlaylistRepository, PlaylistSongRepository
from repository.song_repo import SongRepository
from spotify.client import SpotifyClient

logger = logging.getLogger(__name__)


async def push_playlist(ctx: dict, playlist_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            playlist = await PlaylistRepository(session).get_and_lock(playlist_id)
            if not playlist:
                logger.error(f"Playlist {playlist_id} not found")
                return
            if playlist.pushed_at:
                logger.info(f"Playlist {playlist_id} already fully pushed, skipping")
                return

        playlist_repo = PlaylistRepository(session)
        song_repo = SongRepository(session)
        ps_repo = PlaylistSongRepository(session)

        songs = await playlist_repo.get_songs_for_playlist(playlist_id)
        if not songs:
            logger.warning(f"Playlist {playlist_id} has no songs, skipping")
            return

        async with httpx.AsyncClient() as client:
            spotify = SpotifyClient(client)
            await spotify.ensure_token()

            # if spotify_id already set from a previous partial attempt, reuse it
            if not playlist.spotify_id:
                playlist_name = f"Death Guild - {playlist.date}"
                spotify_playlist_id = await spotify.create_playlist(playlist_name)
                await playlist_repo.set_spotify_id(playlist_id, spotify_playlist_id)
                logger.info(f"Created Spotify playlist '{playlist_name}' ({spotify_playlist_id})")
            else:
                spotify_playlist_id = playlist.spotify_id
                logger.info(f"Resuming partial push for playlist {playlist.date}")

            existing_track_ids = []
            new_track_ids = []
            for ps, song in songs:
                if ps.spotify_track_id:
                    existing_track_ids.append(ps.spotify_track_id)
                    continue

                spotify_id = song.spotify_id
                if not spotify_id:
                    result = await spotify.search_track(song.artist, song.title)
                    if result:
                        spotify_id = result.track_id
                        await song_repo.set_spotify_id(song.id, spotify_id)
                    else:
                        logger.info(f"No Spotify match: {song.artist} - {song.title}")
                        continue

                await ps_repo.set_spotify_track_id(ps.id, spotify_id)
                new_track_ids.append(spotify_id)

            if new_track_ids:
                await spotify.add_tracks(spotify_playlist_id, new_track_ids)

            await playlist_repo.mark_pushed(playlist_id)
            logger.info(
                f"Pushed playlist {playlist.date}: "
                f"{len(existing_track_ids) + len(new_track_ids)}/{len(songs)} songs matched"
            )


class WorkerSettings:
    functions = [push_playlist]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 3600
    retry_jobs = True
    max_tries = 5
