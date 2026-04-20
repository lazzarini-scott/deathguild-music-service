"""Seed Render database from seed_data.json.gz. Runs on every deploy — truncates and reloads."""
import asyncio
import gzip
import json
import logging
import os
from datetime import date, datetime

from sqlalchemy import text
from core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SEED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seed_data.json.gz")


async def seed():
    if not os.path.exists(SEED_FILE):
        logger.info("No seed_data.json.gz found, skipping.")
        return

    logger.info("Loading seed data...")
    with gzip.open(SEED_FILE, "rt") as f:
        data = json.load(f)

    songs = data["songs"]
    playlists = data["playlists"]
    playlist_songs = data["playlist_songs"]

    # Parse dates
    for song in songs:
        if song["spotify_searched_at"]:
            song["spotify_searched_at"] = datetime.fromisoformat(song["spotify_searched_at"])
    for p in playlists:
        p["date"] = date.fromisoformat(p["date"])
        if p["scraped_at"]: p["scraped_at"] = datetime.fromisoformat(p["scraped_at"])
        if p["pushed_at"]: p["pushed_at"] = datetime.fromisoformat(p["pushed_at"])

    async with AsyncSessionLocal() as session:
        # Truncate in dependency order
        await session.execute(text("TRUNCATE playlist_songs, playlists, songs RESTART IDENTITY CASCADE"))
        await session.commit()

        for i in range(0, len(songs), 500):
            await session.execute(
                text("INSERT INTO songs (id, artist, title, spotify_id, spotify_searched_at) "
                     "VALUES (:id, :artist, :title, :spotify_id, :spotify_searched_at)"),
                songs[i:i+500],
            )
            await session.commit()
        logger.info("Inserted %d songs", len(songs))

        for i in range(0, len(playlists), 500):
            await session.execute(
                text("INSERT INTO playlists (id, date, spotify_id, scraped_at, pushed_at) "
                     "VALUES (:id, :date, :spotify_id, :scraped_at, :pushed_at)"),
                playlists[i:i+500],
            )
            await session.commit()
        logger.info("Inserted %d playlists", len(playlists))

        for i in range(0, len(playlist_songs), 500):
            await session.execute(
                text("INSERT INTO playlist_songs (id, playlist_id, song_id, position, is_request, spotify_track_id) "
                     "VALUES (:id, :playlist_id, :song_id, :position, :is_request, :spotify_track_id)"),
                playlist_songs[i:i+500],
            )
            await session.commit()
        logger.info("Inserted %d playlist_songs", len(playlist_songs))

        # Reset sequences
        await session.execute(text("SELECT setval('songs_id_seq', (SELECT MAX(id) FROM songs))"))
        await session.execute(text("SELECT setval('playlists_id_seq', (SELECT MAX(id) FROM playlists))"))
        await session.execute(text("SELECT setval('playlist_songs_id_seq', (SELECT MAX(id) FROM playlist_songs))"))
        await session.commit()

    logger.info("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
