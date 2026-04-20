import asyncio
import logging

from core.database import AsyncSessionLocal, init_db
from scraper.client import ScraperClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        client = ScraperClient(session)
        await client.run()


if __name__ == "__main__":
    asyncio.run(main())
