"""Formal API endpoint tests for users, digest generation, boost, and retrieval."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.activity_item import ActivityItem
from app.models.digest import Digest
from app.models.digest_item import DigestItem
from tests.conftest import test_async_session


@pytest.mark.anyio
async def test_health_check_endpoint(async_client: AsyncClient):
    """Test that GET /health still returns status ok."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_get_users_endpoint(async_client: AsyncClient):
    """Test that GET /api/users returns the list of seeded users."""
    response = await async_client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) == 3

    user_ids = [u["id"] for u in data["users"]]
    assert "user_1" in user_ids
    assert "user_2" in user_ids
    assert "user_3" in user_ids


@pytest.mark.anyio
async def test_post_digest_valid_user(async_client: AsyncClient):
    """Test that POST /api/digest/user_1 generates and returns a valid 5-item AI digest."""
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)

    response = await async_client.post("/api/digest/user_1")
    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "user_1"
    assert data["week_identifier"] == "2026-W30"
    assert "summary_prose" in data
    assert len(data["items"]) == 5

    # Verify generated_at is a recent real-time timestamp (within 60s of now)
    gen_at = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
    assert abs((now_utc - gen_at).total_seconds()) < 60

    first_item = data["items"][0]
    assert "activity_item_id" in first_item
    assert first_item["activity_item_id"].startswith("ai_act_")
    assert "title" in first_item
    assert "explanation_text" in first_item


@pytest.mark.anyio
async def test_post_digest_user_with_no_tag_overlap(async_client: AsyncClient):
    """Test POST /api/digest/user_3 for a user with zero interest overlap receives 5 AI items."""
    response = await async_client.post("/api/digest/user_3")
    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "user_3"
    assert data["week_identifier"] == "2026-W30"
    assert "summary_prose" in data
    assert len(data["items"]) == 5

    for item in data["items"]:
        assert len(item["title"]) > 0
        assert len(item["explanation_text"]) > 0


@pytest.mark.anyio
async def test_post_digest_nonexistent_user(async_client: AsyncClient):
    """Test that POST /api/digest/nonexistent_user returns 404."""
    response = await async_client.post("/api/digest/nonexistent_user")
    assert response.status_code == 404
    assert "User 'nonexistent_user' not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_digest_after_post(async_client: AsyncClient):
    """Test that GET /api/digest/user_1 after POST returns the persisted digest."""
    post_res = await async_client.post("/api/digest/user_1")
    assert post_res.status_code == 200
    post_data = post_res.json()

    get_res = await async_client.get("/api/digest/user_1")
    assert get_res.status_code == 200
    get_data = get_res.json()

    assert get_data["id"] == post_data["id"]
    assert get_data["user_id"] == "user_1"
    assert get_data["summary_prose"] == post_data["summary_prose"]
    assert len(get_data["items"]) == 5
    assert "section_title" in get_data["items"][0]
    assert get_data["items"][0]["section_title"] is not None


@pytest.mark.anyio
async def test_get_digest_no_digest_exists(async_client: AsyncClient):
    """Test that GET /api/digest/user_2 returns 404 when no digest has been generated yet."""
    response = await async_client.get("/api/digest/user_2")
    assert response.status_code == 404
    assert "No digest found for user 'user_2'" in response.json()["detail"]


@pytest.mark.anyio
async def test_post_digest_upsert_prevents_duplicate_digest(async_client: AsyncClient):
    """Test that calling POST /api/digest/user_1 twice upserts and does NOT create duplicate digests."""
    res1 = await async_client.post("/api/digest/user_1")
    assert res1.status_code == 200

    res2 = await async_client.post("/api/digest/user_1")
    assert res2.status_code == 200

    async with test_async_session() as session:
        stmt = select(func.count(Digest.id)).where(Digest.user_id == "user_1")
        count_result = await session.execute(stmt)
        digest_count = count_result.scalar()

        assert digest_count == 1


@pytest.mark.anyio
async def test_post_digest_query_params_supported(async_client: AsyncClient):
    """Test POST /api/digest/user_1 with optional query params (diversity, mode) returns 5 items via unified path."""
    response = await async_client.post("/api/digest/user_1?diversity=true&mode=standard")
    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "user_1"
    assert len(data["items"]) == 5


@pytest.mark.anyio
async def test_post_digest_boost_endpoint_persists_items(async_client: AsyncClient):
    """Test POST /api/digest/user_1/boost with an open-ended tag generates and persists boosted items."""
    boost_payload = {"tag": "Quantum Error Correction"}
    response = await async_client.post("/api/digest/user_1/boost", json=boost_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["boost_tag"] == "Quantum Error Correction"
    assert len(data["items"]) == 5

    first_item = data["items"][0]
    assert first_item["activity_item_id"].startswith("boost_act_")

    # Assert that boosted activity items exist in database for FK validity
    async with test_async_session() as session:
        act_res = await session.execute(
            select(ActivityItem).where(ActivityItem.id == first_item["activity_item_id"])
        )
        act_item = act_res.scalar_one_or_none()
        assert act_item is not None
        assert act_item.is_ai_generated is True


@pytest.mark.anyio
async def test_per_user_cleanup_scoping_prevents_deleting_other_users_items(
    async_client: AsyncClient,
):
    """Verify regenerating User 1's digest purges User 1's stale items, but leaves User 2's items 100% intact."""
    # 1. Generate digest for User 1
    res1 = await async_client.post("/api/digest/user_1")
    assert res1.status_code == 200
    u1_items = res1.json()["items"]
    u1_act_ids_v1 = [it["activity_item_id"] for it in u1_items]

    # 2. Generate digest for User 2
    res2 = await async_client.post("/api/digest/user_2")
    assert res2.status_code == 200
    u2_items = res2.json()["items"]
    u2_act_ids = [it["activity_item_id"] for it in u2_items]

    # 3. Regenerate digest for User 1
    res1_re = await async_client.post("/api/digest/user_1")
    assert res1_re.status_code == 200

    # 4. Verify DB state:
    async with test_async_session() as session:
        # User 1's v1 old items should be deleted by scoped cleanup
        u1_old_res = await session.execute(
            select(ActivityItem).where(ActivityItem.id.in_(u1_act_ids_v1))
        )
        assert len(u1_old_res.scalars().all()) == 0

        # User 2's items MUST still exist intact in DB
        u2_res = await session.execute(
            select(ActivityItem).where(ActivityItem.id.in_(u2_act_ids))
        )
        assert len(u2_res.scalars().all()) == len(u2_act_ids)

        # User 2's Digest and DigestItems MUST still exist intact in DB
        u2_digest_res = await session.execute(
            select(Digest).where(Digest.user_id == "user_2")
        )
        assert u2_digest_res.scalar_one_or_none() is not None

