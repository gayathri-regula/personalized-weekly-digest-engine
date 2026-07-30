"""Read-only audit script for digests and digest_items tables in the database."""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

# Load backend/.env
backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(backend_dir / ".env")

KNOWN_USER_IDS = {"user_1", "user_2", "user_3", "user_4", "user_5"}


async def audit_digests() -> None:
    """Audit digests and digest_items tables."""
    raw_db_url = os.getenv("DATABASE_URL", "")
    if not raw_db_url:
        print("[ERROR] DATABASE_URL environment variable is missing.")
        sys.exit(1)

    db_url = raw_db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url, statement_cache_size=0)

    try:
        print("==========================================")
        print("DATABASE DIGESTS & DIGEST_ITEMS AUDIT REPORT")
        print("==========================================\n")

        # 1. Audit digests table
        digest_rows = await conn.fetch(
            "SELECT id, user_id, week_identifier, generated_at FROM digests ORDER BY generated_at DESC"
        )

        print(f"--- DIGESTS TABLE (Total Rows: {len(digest_rows)}) ---")
        if not digest_rows:
            print("No rows found in 'digests' table.")
        else:
            invalid_digests_count = 0
            for row in digest_rows:
                d_id = row["id"]
                u_id = row["user_id"]
                w_id = row["week_identifier"]
                g_at = row["generated_at"]

                is_known = u_id in KNOWN_USER_IDS
                flag_str = "" if is_known else "  <-- [FLAGGED: UNKNOWN/UNRELATED USER ID]"
                if not is_known:
                    invalid_digests_count += 1

                print(
                    f"ID: {d_id:<30} | User: {u_id:<12} | Week: {w_id:<10} | Generated: {g_at}{flag_str}"
                )

            if invalid_digests_count > 0:
                print(f"\n[ALERT] Found {invalid_digests_count} digest row(s) for unknown user IDs.")
            else:
                print("\n[OK] All digest user IDs match known production users (user_1 .. user_5).")

        print("\n------------------------------------------\n")

        # 2. Audit digest_items table
        total_items_row = await conn.fetchrow("SELECT COUNT(*) FROM digest_items")
        total_items_count = total_items_row[0] if total_items_row else 0

        grouped_items = await conn.fetch(
            "SELECT digest_id, COUNT(*) as item_count FROM digest_items GROUP BY digest_id ORDER BY digest_id"
        )

        print(f"--- DIGEST_ITEMS TABLE ---")
        print(f"Total Rows Count: {total_items_count}")
        print("\nBreakdown by digest_id:")

        if not grouped_items:
            print("No rows found in 'digest_items' table.")
        else:
            for g_row in grouped_items:
                d_id = g_row["digest_id"]
                ic_count = g_row["item_count"]
                print(f"  digest_id: {d_id:<30} | Item Count: {ic_count}")

        print("\n==========================================")
        print("AUDIT COMPLETE (Read-Only)")
        print("==========================================")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(audit_digests())
