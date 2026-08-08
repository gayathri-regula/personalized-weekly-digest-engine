"""Migration script to add item_feedback table to database."""

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
        print("Creating item_feedback table if not exists...")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS item_feedback (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                activity_item_id VARCHAR NOT NULL REFERENCES activity_items(id) ON DELETE CASCADE,
                feedback_type VARCHAR NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                CONSTRAINT uq_user_activity_feedback UNIQUE (user_id, activity_item_id)
            );
            """
        )
        print("Migration completed successfully: item_feedback table is ready.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
