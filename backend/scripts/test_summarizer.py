"""Manual verification script for summarizer service against real Supabase dataset."""

import asyncio
import os
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
from app.services.summarizer import generate_digest_summary


async def verify_summarizer_on_supabase() -> None:
    """Fetch users and items, run ranker, and test summarizer on both LLM and fallback paths."""
    api_key_present = bool(os.getenv("ANTHROPIC_API_KEY"))

    print("==================================================")
    print("PERSONALIZED DIGEST ENGINE - SUMMARIZER VERIFICATION")
    print("==================================================")
    print(f"ANTHROPIC_API_KEY Present: {api_key_present}")
    if api_key_present:
        print(" -> LLM Path will attempt calling Anthropic Claude API.")
    else:
        print(" -> LLM Path will automatically fall back to template summary (no API key).")
    print("==================================================\n")

    async with async_session_factory() as session:
        # Fetch 3 users
        users_result = await session.execute(select(User).order_by(User.id).limit(3))
        users = users_result.scalars().all()

        # Fetch all activity items
        items_result = await session.execute(
            select(ActivityItem).order_by(ActivityItem.created_at.desc())
        )
        items = items_result.scalars().all()
        items_by_id = {item.id: item for item in items}

        reference_now = datetime(2026, 7, 27, 23, 59, 59, tzinfo=timezone.utc)

        for user in users:
            print("--------------------------------------------------")
            print(f"USER: {user.name} (ID: {user.id})")
            print(f"INTEREST TAGS: {user.interest_tags}")
            print("--------------------------------------------------")

            # Step 1: Rank items for user
            ranked_items = rank_items_for_user(
                user=user, items=items, top_n=5, now=reference_now
            )

            # Step 2: Join ranked items with ActivityItem details
            joined_items = []
            for r in ranked_items:
                item_obj = items_by_id.get(r.activity_item_id)
                joined_items.append(
                    {
                        "activity_item_id": r.activity_item_id,
                        "relevance_score": r.relevance_score,
                        "explanation_text": r.explanation_text,
                        "rank_position": r.rank_position,
                        "title": item_obj.title if item_obj else "Untitled",
                        "content": item_obj.content if item_obj else "",
                        "category_tags": item_obj.category_tags if item_obj else [],
                    }
                )

            # Step 3: Run LLM path (use_llm=True)
            print("\n--- [PATH 1: LLM Path (use_llm=True)] ---")
            summary_llm = generate_digest_summary(
                user_name=user.name,
                ranked_items_with_details=joined_items,
                use_llm=True,
            )
            print(summary_llm)

            # Step 4: Run Fallback path (use_llm=False) for verification
            print("\n--- [PATH 2: Template Fallback Path (use_llm=False)] ---")
            summary_fallback = generate_digest_summary(
                user_name=user.name,
                ranked_items_with_details=joined_items,
                use_llm=False,
            )
            print(summary_fallback)
            print()

        print("==================================================")
        print("SUMMARIZER VERIFICATION COMPLETE: Both paths demonstrated.")
        print("==================================================")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_summarizer_on_supabase())
