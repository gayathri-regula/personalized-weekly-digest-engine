"""Manual verification script for ranker service against real Supabase dataset."""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.db.session import async_session_factory, engine
from app.models import ActivityItem, User
from app.services.ranker import rank_items_for_user


async def verify_ranker_on_supabase() -> None:
    """Fetch users and activity items from Supabase and display top-5 digests for all users."""
    async with async_session_factory() as session:
        # Fetch all users
        users_result = await session.execute(select(User).order_by(User.id))
        users = users_result.scalars().all()

        # Fetch all activity items
        items_result = await session.execute(
            select(ActivityItem).order_by(ActivityItem.created_at.desc())
        )
        items = items_result.scalars().all()

        print("==================================================")
        print("PERSONALIZED DIGEST ENGINE - RANKER VERIFICATION")
        print("==================================================")
        print(f"Loaded {len(users)} users and {len(items)} activity items from database.\n")

        # Fixed reference time corresponding to the dataset's target week endpoint
        reference_now = datetime(2026, 7, 27, 23, 59, 59, tzinfo=timezone.utc)

        user_top_item_ids = {}

        for user in users:
            print("--------------------------------------------------")
            print(f"USER: {user.name} (ID: {user.id})")
            print(f"INTEREST TAGS: {user.interest_tags}")
            print("--------------------------------------------------")

            ranked_items = rank_items_for_user(
                user=user, items=items, top_n=5, now=reference_now
            )

            # Record top item IDs to verify distinct digests
            user_top_item_ids[user.id] = [r.activity_item_id for r in ranked_items]

            # Map items by ID for title output
            items_by_id = {item.id: item for item in items}

            for r in ranked_items:
                item_obj = items_by_id.get(r.activity_item_id)
                title = item_obj.title if item_obj else "Unknown Title"
                category_tags = item_obj.category_tags if item_obj else []

                print(f"  Rank {r.rank_position}: [Score: {r.relevance_score:.4f}] {r.activity_item_id}")
                print(f"    Title: {title}")
                print(f"    Tags: {category_tags}")
                print(f"    Explanation: {r.explanation_text}")
                print()

        # Verify distinct digests
        unique_digests = len(set(tuple(ids) for ids in user_top_item_ids.values()))
        print("==================================================")
        print(f"VERIFICATION SUMMARY: {unique_digests} of {len(users)} users have unique top-5 digests.")
        print("==================================================")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_ranker_on_supabase())
