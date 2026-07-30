"""Script to inspect, purge contaminated data, and reload production dataset."""

import asyncio
import json
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func, delete
from app.db.session import async_session_factory, engine
from app.models import ActivityItem, User, Digest, DigestItem
from scripts.load_dataset import load_dataset


async def main():
    async with async_session_factory() as session:
        print("==========================================")
        print("STEP 1: INSPECTING PRODUCTION DATABASE")
        print("==========================================")
        count_before = (await session.execute(select(func.count(ActivityItem.id)))).scalar()
        print(f"Current activity_items count: {count_before}")
        
        stmt = select(ActivityItem.id, ActivityItem.title, ActivityItem.category_tags).limit(3)
        first_3 = (await session.execute(stmt)).all()
        print("First 3 rows in activity_items:")
        for idx, row in enumerate(first_3, start=1):
            print(f"  {idx}. ID: {row.id} | Title: {row.title} | Tags: {row.category_tags}")
        print()

        print("==========================================")
        print("STEP 2 & 3: PURGING CONTAMINATED DATA")
        print("==========================================")
        # Delete digest_items first (foreign key reference to digests & activity_items)
        del_di = await session.execute(delete(DigestItem))
        print(f"Deleted digest_items rows: {del_di.rowcount}")

        # Delete digests
        del_d = await session.execute(delete(Digest))
        print(f"Deleted digests rows: {del_d.rowcount}")

        # Delete activity_items
        del_ai = await session.execute(delete(ActivityItem))
        print(f"Deleted activity_items rows: {del_ai.rowcount}")

        await session.commit()

        # Confirm count after deletion
        count_after_del = (await session.execute(select(func.count(ActivityItem.id)))).scalar()
        print(f"Confirmed activity_items count after deletion: {count_after_del}")
        print()

    print("==========================================")
    print("STEP 4: RELOADING VERIFIED DATASET")
    print("==========================================")
    await load_dataset()

    async with async_session_factory() as session:
        items_count_final = (await session.execute(select(func.count(ActivityItem.id)))).scalar()
        print(f"Final activity_items count in production DB: {items_count_final}")

        print("\nVerifying 5 registered users and interest_tags:")
        users = (await session.execute(select(User))).scalars().all()
        for u in users:
            print(f"  User ID: {u.id} | Name: {u.name} | Interest Tags: {u.interest_tags}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
