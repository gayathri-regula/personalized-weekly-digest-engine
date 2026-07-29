"""Formal API endpoint tests for users, digest generation, and retrieval."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.digest import Digest
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
    """Test that POST /api/digest/user_1 generates and returns a valid digest."""
    response = await async_client.post("/api/digest/user_1")
    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "user_1"
    assert data["week_identifier"] == "2026-W30"
    assert "summary_prose" in data
    assert len(data["items"]) > 0

    first_item = data["items"][0]
    assert "activity_item_id" in first_item
    assert "title" in first_item
    assert "explanation_text" in first_item


@pytest.mark.anyio
async def test_post_digest_no_tag_overlap_triggers_popular_fallback(
    async_client: AsyncClient,
):
    """Test POST /api/digest/user_3 for a user with zero interest overlap.

    Per ARCHITECTURE.md Section 10.1, items with zero tag match can still qualify
    if their recency + engagement exceed 0.10, triggering the 'popular activity item
    in your network this week' explanation fallback without erroring.
    """
    response = await async_client.post("/api/digest/user_3")
    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "user_3"
    assert data["week_identifier"] == "2026-W30"
    assert "summary_prose" in data

    # Popular fallback items are included if score >= 0.10
    for item in data["items"]:
        assert item["explanation_text"] == "popular activity item in your network this week"


@pytest.mark.anyio
async def test_post_digest_nonexistent_user(async_client: AsyncClient):
    """Test that POST /api/digest/nonexistent_user returns 404."""
    response = await async_client.post("/api/digest/nonexistent_user")
    assert response.status_code == 404
    assert "User 'nonexistent_user' not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_digest_after_post(async_client: AsyncClient):
    """Test that GET /api/digest/user_1 after POST returns the persisted digest."""
    # First generate digest
    post_res = await async_client.post("/api/digest/user_1")
    assert post_res.status_code == 200
    post_data = post_res.json()

    # Then retrieve digest
    get_res = await async_client.get("/api/digest/user_1")
    assert get_res.status_code == 200
    get_data = get_res.json()

    assert get_data["id"] == post_data["id"]
    assert get_data["user_id"] == "user_1"
    assert get_data["summary_prose"] == post_data["summary_prose"]
    assert len(get_data["items"]) == len(post_data["items"])


@pytest.mark.anyio
async def test_get_digest_no_digest_exists(async_client: AsyncClient):
    """Test that GET /api/digest/user_2 returns 404 when no digest has been generated yet."""
    response = await async_client.get("/api/digest/user_2")
    assert response.status_code == 404
    assert "No digest found for user 'user_2'" in response.json()["detail"]


@pytest.mark.anyio
async def test_post_digest_upsert_prevents_duplicate_digest(async_client: AsyncClient):
    """Test that calling POST /api/digest/user_1 twice upserts and does NOT create duplicates."""
    # First POST
    res1 = await async_client.post("/api/digest/user_1")
    assert res1.status_code == 200

    # Second POST
    res2 = await async_client.post("/api/digest/user_1")
    assert res2.status_code == 200

    # Verify direct DB count for user_1
    async with test_async_session() as session:
        stmt = select(func.count(Digest.id)).where(Digest.user_id == "user_1")
        count_result = await session.execute(stmt)
        digest_count = count_result.scalar()

        assert digest_count == 1
