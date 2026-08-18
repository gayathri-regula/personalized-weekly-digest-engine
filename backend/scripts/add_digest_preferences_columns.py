"""Migration script to add digest_frequency, content_length, and digest_language columns to users table."""

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
        print("Adding digest_frequency, content_length, and digest_language columns to users table if not exist...")
        await conn.execute(
            """
            ALTER TABLE users ADD COLUMN IF NOT EXISTS digest_frequency VARCHAR DEFAULT 'weekly';
            ALTER TABLE users ADD COLUMN IF NOT EXISTS content_length VARCHAR DEFAULT 'detailed';
            ALTER TABLE users ADD COLUMN IF NOT EXISTS digest_language VARCHAR DEFAULT 'en';
            """
        )
        print("Migration completed successfully: digest preferences columns are ready.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
