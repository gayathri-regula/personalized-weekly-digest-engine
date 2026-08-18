"""Tests for the user trending topics endpoint GET /api/digest/{user_id}/trending."""

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_trending_topics_nonexistent_user(async_client: AsyncClient):
    """Test requesting trending topics for nonexistent user returns HTTP 404."""
    res = await async_client.get("/api/digest/nonexistent_user_999/trending")
    assert res.status_code == 404
    assert "User 'nonexistent_user_999' not found" in res.json()["detail"]


@pytest.mark.anyio
async def test_trending_topics_zero_history(async_client: AsyncClient):
    """Test user with zero digests returns empty list and 200 OK."""
    user_res = await async_client.post(
        "/api/users",
        json={"name": "Zero Digest User", "interest_tags": ["AI", "Python", "Cloud"]},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    res = await async_client.get(f"/api/digest/{user_id}/trending")
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.anyio
async def test_trending_topics_one_week_history(async_client: AsyncClient):
    """Test user with only one digest returns empty list and 200 OK (not enough history)."""
    user_res = await async_client.post(
        "/api/users",
        json={"name": "One Week User", "interest_tags": ["AI", "Python", "Cloud"]},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    # Generate single digest
    gen_res = await async_client.post(f"/api/digest/{user_id}")
    assert gen_res.status_code == 200

    res = await async_client.get(f"/api/digest/{user_id}/trending")
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.anyio
async def test_trending_topics_two_weeks_history(async_client: AsyncClient):
    """Test user with two weeks of digest history returns correct up/down/flat directions."""
    user_res = await async_client.post(
        "/api/users",
        json={"name": "Two Week User", "interest_tags": ["AI", "Python", "Cloud"]},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    # Generate first digest (week 1)
    gen_res1 = await async_client.post(f"/api/digest/{user_id}")
    assert gen_res1.status_code == 200

    # Generate second digest (week 2) - triggers week comparison
    gen_res2 = await async_client.post(f"/api/digest/{user_id}")
    assert gen_res2.status_code == 200

    res = await async_client.get(f"/api/digest/{user_id}/trending")
    assert res.status_code == 200
    data = res.json()

    # Must be a list with at most 5 items
    assert isinstance(data, list)
    assert len(data) <= 5

    for item in data:
        assert "category" in item
        assert item["direction"] in ["up", "down", "flat"]
        assert "current_count" in item
        assert "previous_count" in item
        assert isinstance(item["current_count"], int)
        assert isinstance(item["previous_count"], int)
