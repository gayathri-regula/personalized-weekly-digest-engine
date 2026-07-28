"""Dataset loader script to insert Phase 4 users and activity items into Postgres."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.db.session import async_session_factory, engine
from app.models import ActivityItem, User

DATA_DIR = backend_dir / "data"


async def load_dataset() -> None:
    """Load users.json and activity_items.json into database idempotently."""
    async with async_session_factory() as session:
        # Load Users
        users_file = DATA_DIR / "users.json"
        with open(users_file, "r", encoding="utf-8") as f:
            users_data = json.load(f)

        users_inserted = 0
        users_existing = 0

        for u_data in users_data:
            stmt = select(User).where(User.id == u_data["id"])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user is None:
                user = User(
                    id=u_data["id"],
                    name=u_data["name"],
                    interest_tags=u_data["interest_tags"],
                )
                session.add(user)
                users_inserted += 1
            else:
                users_existing += 1

        # Load Activity Items
        items_file = DATA_DIR / "activity_items.json"
        with open(items_file, "r", encoding="utf-8") as f:
            items_data = json.load(f)

        items_inserted = 0
        items_existing = 0

        for i_data in items_data:
            stmt = select(ActivityItem).where(ActivityItem.id == i_data["id"])
            result = await session.execute(stmt)
            existing_item = result.scalar_one_or_none()

            if existing_item is None:
                created_at_dt = datetime.fromisoformat(
                    i_data["created_at"].replace("Z", "+00:00")
                )
                item = ActivityItem(
                    id=i_data["id"],
                    title=i_data["title"],
                    content=i_data["content"],
                    category_tags=i_data["category_tags"],
                    created_at=created_at_dt,
                    engagement_metadata=i_data["engagement_metadata"],
                )
                session.add(item)
                items_inserted += 1
            else:
                items_existing += 1

        await session.commit()

        print(
            f"Users: {users_inserted} inserted, {users_existing} already existing."
        )
        print(
            f"Activity Items: {items_inserted} inserted, {items_existing} already existing."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(load_dataset())
