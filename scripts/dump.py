"""Export local database to seed_data.json.gz for deployment."""
import asyncio
import gzip
import json

from sqlalchemy import text
from core.database import AsyncSessionLocal


async def dump():
    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT id, artist, title, spotify_id, spotify_searched_at FROM songs ORDER BY id"))
        songs = [dict(row._mapping) for row in r]
        for song in songs:
            if song["spotify_searched_at"]:
                song["spotify_searched_at"] = song["spotify_searched_at"].isoformat()

        r = await s.execute(text("SELECT id, date, spotify_id, scraped_at, pushed_at FROM playlists ORDER BY id"))
        playlists = [dict(row._mapping) for row in r]
        for p in playlists:
            p["date"] = p["date"].isoformat()
            if p["scraped_at"]: p["scraped_at"] = p["scraped_at"].isoformat()
            if p["pushed_at"]: p["pushed_at"] = p["pushed_at"].isoformat()

        r = await s.execute(text("SELECT id, playlist_id, song_id, position, is_request, spotify_track_id FROM playlist_songs ORDER BY id"))
        ps = [dict(row._mapping) for row in r]

        data = {"songs": songs, "playlists": playlists, "playlist_songs": ps}
        with gzip.open("seed_data.json.gz", "wt") as f:
            json.dump(data, f)
        print(f"Exported {len(songs)} songs, {len(playlists)} playlists, {len(ps)} playlist_songs")


if __name__ == "__main__":
    asyncio.run(dump())
