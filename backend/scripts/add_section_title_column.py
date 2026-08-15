"""Migration script to add section_title VARCHAR column to activity_items table."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")

import asyncpg


async def migrate() -> None:
    raw_url = os.getenv("DATABASE_URL", "")
    if not raw_url:
        print("Error: DATABASE_URL not set in environment.")
        sys.exit(1)

    url = raw_url.replace("postgresql+asyncpg://", "postgres://").replace("postgresql://", "postgres://")
    conn = await asyncpg.connect(url, statement_cache_size=0)
    try:
        print("Adding section_title column to activity_items table if not exists...")
        await conn.execute(
            "ALTER TABLE activity_items ADD COLUMN IF NOT EXISTS section_title VARCHAR;"
        )
        print("Migration completed successfully: section_title column is ready.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
