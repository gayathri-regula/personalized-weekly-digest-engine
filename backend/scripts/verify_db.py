"""Verification script to query row counts and sample rows from the database."""

import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import func, select
from app.db.session import async_session_factory, engine
from app.models import ActivityItem, User


async def verify_db() -> None:
    """Query total row counts and sample rows from users and activity_items tables."""
    async with async_session_factory() as session:
        # Total counts
        user_count = (await session.execute(select(func.count(User.id)))).scalar()
        item_count = (await session.execute(select(func.count(ActivityItem.id)))).scalar()

        print(f"Total Users Count: {user_count}")
        print(f"Total Activity Items Count: {item_count}")
        print("-" * 50)

        # Sample user
        sample_user = (await session.execute(select(User).limit(1))).scalar_one()
        print("Sample User Row:")
        print(f"  id: {sample_user.id}")
        print(f"  name: {sample_user.name}")
        print(f"  interest_tags: {sample_user.interest_tags}")
        print("-" * 50)

        # Sample activity item
        sample_item = (await session.execute(select(ActivityItem).limit(1))).scalar_one()
        print("Sample Activity Item Row:")
        print(f"  id: {sample_item.id}")
        print(f"  title: {sample_item.title}")
        print(f"  content: {sample_item.content[:100]}...")
        print(f"  category_tags: {sample_item.category_tags}")
        print(f"  created_at: {sample_item.created_at}")
        print(f"  engagement_metadata: {json.dumps(sample_item.engagement_metadata)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_db())
