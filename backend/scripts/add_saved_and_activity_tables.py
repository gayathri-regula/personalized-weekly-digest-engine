"""Migration script to add saved_items and activity_log tables to database."""

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
        print("Creating saved_items and activity_log tables if not exist...")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_items (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                activity_item_id VARCHAR NOT NULL REFERENCES activity_items(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_user_saved_item UNIQUE (user_id, activity_item_id)
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                event_type VARCHAR NOT NULL,
                description VARCHAR NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_activity_log_user_created ON activity_log(user_id, created_at DESC);
            """
        )
        print("Migration completed successfully: saved_items and activity_log tables are ready.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
