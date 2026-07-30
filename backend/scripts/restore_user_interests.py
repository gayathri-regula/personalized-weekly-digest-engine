"""Script to restore user interest_tags in the database from backend/data/users.json."""

import asyncio
import json
import os
import sys
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

# Load backend/.env
backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")

DATA_FILE = backend_dir / "data" / "users.json"


async def restore_user_interests() -> None:
    """Restore interest_tags for all users in PostgreSQL from users.json."""
    if not DATA_FILE.exists():
        print(f"[ERROR] Source file missing: {DATA_FILE}")
        sys.exit(1)

    raw_db_url = os.getenv("DATABASE_URL", "")
    if not raw_db_url:
        print("[ERROR] DATABASE_URL environment variable is missing.")
        sys.exit(1)

    # Normalize connection string for asyncpg
    db_url = raw_db_url.replace("postgresql+asyncpg://", "postgresql://")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users_data = json.load(f)

    print("==========================================")
    print("RESTORING USER INTEREST TAGS FROM JSON SOURCE OF TRUTH")
    print(f"Source file: {DATA_FILE}")
    print("==========================================\n")

    conn = await asyncpg.connect(db_url)

    try:
        updated_count = 0
        missing_count = 0

        for u_data in users_data:
            user_id = u_data["id"]
            user_name = u_data.get("name", "")
            target_tags = u_data.get("interest_tags", [])

            # Fetch existing row
            row = await conn.fetchrow(
                "SELECT id, name, interest_tags FROM users WHERE id = $1", user_id
            )

            if row is None:
                print(f"[WARNING] User ID '{user_id}' not found in database. Skipping.")
                missing_count += 1
                continue

            raw_old = row["interest_tags"]
            if isinstance(raw_old, str):
                old_tags = json.loads(raw_old)
            elif isinstance(raw_old, list):
                old_tags = raw_old
            else:
                old_tags = list(raw_old) if raw_old is not None else []

            # Update existing row's interest_tags unconditionally
            tags_json_str = json.dumps(target_tags)
            await conn.execute(
                "UPDATE users SET interest_tags = $1::json WHERE id = $2",
                tags_json_str,
                user_id,
            )
            updated_count += 1

            print(f"User ID: {user_id} ({row['name']})")
            print(f"  BEFORE : {old_tags}")
            print(f"  AFTER  : {target_tags}")
            print("------------------------------------------")

        print("\n==========================================")
        print(f"SUMMARY: {updated_count} user interest_tags updated, {missing_count} users missing.")
        print("==========================================")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(restore_user_interests())
