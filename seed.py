import asyncio
import json
import logging
import os
from datetime import date, datetime

from sqlalchemy import text
from core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SEED_DIR = os.path.join(os.path.dirname(__file__), "seed_data")


async def seed():
    if not os.path.exists(SEED_DIR):
        logger.info("No seed_data directory, skipping seed.")
        return

    async with AsyncSessionLocal() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM songs"))
        if result.scalar() > 0:
            logger.info("Database already has data, skipping seed.")
            return

        logger.info("Seeding database...")

        with open(os.path.join(SEED_DIR, "songs.json")) as f:
            songs = json.load(f)
        with open(os.path.join(SEED_DIR, "playlists.json")) as f:
            playlists = json.load(f)
        with open(os.path.join(SEED_DIR, "playlist_songs.json")) as f:
            playlist_songs = json.load(f)

        # Insert songs
        for song in songs:
            if song['spotify_searched_at']:
                song['spotify_searched_at'] = datetime.fromisoformat(song['spotify_searched_at'])
        for i in range(0, len(songs), 500):
            batch = songs[i:i+500]
            await session.execute(
                text("INSERT INTO songs (id, artist, title, spotify_id, spotify_searched_at) "
                     "VALUES (:id, :artist, :title, :spotify_id, :spotify_searched_at) "
                     "ON CONFLICT DO NOTHING"),
                batch,
            )
            await session.commit()
        logger.info("Inserted %d songs", len(songs))

        # Insert playlists
        for p in playlists:
            p['date'] = date.fromisoformat(p['date'])
            if p['scraped_at']: p['scraped_at'] = datetime.fromisoformat(p['scraped_at'])
            if p['pushed_at']: p['pushed_at'] = datetime.fromisoformat(p['pushed_at'])
        for i in range(0, len(playlists), 500):
            batch = playlists[i:i+500]
            await session.execute(
                text("INSERT INTO playlists (id, date, spotify_id, scraped_at, pushed_at) "
                     "VALUES (:id, :date, :spotify_id, :scraped_at, :pushed_at) "
                     "ON CONFLICT DO NOTHING"),
                batch,
            )
            await session.commit()
        logger.info("Inserted %d playlists", len(playlists))

        # Insert playlist_songs
        for i in range(0, len(playlist_songs), 500):
            batch = playlist_songs[i:i+500]
            await session.execute(
                text("INSERT INTO playlist_songs (id, playlist_id, song_id, position, is_request, spotify_track_id) "
                     "VALUES (:id, :playlist_id, :song_id, :position, :is_request, :spotify_track_id) "
                     "ON CONFLICT DO NOTHING"),
                batch,
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
