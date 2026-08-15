"""Tests for updating user interests endpoint PATCH /api/users/{user_id}."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_update_user_interests_valid(async_client: AsyncClient):
    """Test valid update of user_1 interest tags succeeds."""
    payload = {"interest_tags": ["Cloud", "DevOps"]}
    response = await async_client.patch("/api/users/user_1", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "user_1"
    assert data["name"] == "Test User 1"  # Name remains unchanged
    assert data["interest_tags"] == ["Cloud", "DevOps"]


@pytest.mark.anyio
async def test_update_user_interests_nonexistent_user(async_client: AsyncClient):
    """Test updating interests for a nonexistent user returns 404."""
    payload = {"interest_tags": ["Cloud", "DevOps"]}
    response = await async_client.patch("/api/users/user_99999", json=payload)
    assert response.status_code == 404
    assert "User 'user_99999' not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_update_user_interests_tag_count_validation(async_client: AsyncClient):
    """Test updating with < 2 tags returns 422, while 5+ tags succeeds with 200 status code."""
    # 1 tag (too few)
    payload_few = {"interest_tags": ["AI"]}
    res1 = await async_client.patch("/api/users/user_1", json=payload_few)
    assert res1.status_code == 422

    # 5 tags (now valid, no upper cap)
    tags_5 = ["AI", "Python", "Cloud", "DevOps", "Security"]
    payload_many = {
        "interest_tags": tags_5
    }
    res2 = await async_client.patch("/api/users/user_1", json=payload_many)
    assert res2.status_code == 200
    assert res2.json()["interest_tags"] == tags_5


@pytest.mark.anyio
async def test_update_user_interests_unknown_tag(async_client: AsyncClient):
    """Test updating with unknown interest tag returns 400."""
    payload = {"interest_tags": ["AI", "InvalidTagHere"]}
    response = await async_client.patch("/api/users/user_1", json=payload)
    assert response.status_code == 400
    assert "Invalid interest tag 'InvalidTagHere'" in response.json()["detail"]


@pytest.mark.anyio
async def test_update_user_interests_duplicate_tags(async_client: AsyncClient):
    """Test updating with duplicate interest tags returns 400."""
    payload = {"interest_tags": ["Cloud", "Cloud", "DevOps"]}
    response = await async_client.patch("/api/users/user_1", json=payload)
    assert response.status_code == 400
    assert "Duplicate interest tags" in response.json()["detail"]


@pytest.mark.anyio
async def test_update_user_interests_preserves_name_and_id(async_client: AsyncClient):
    """Confirm user id and name are completely unchanged after updating interests."""
    # Fetch initial state
    get_res = await async_client.get("/api/users")
    initial_user = next(u for u in get_res.json()["users"] if u["id"] == "user_2")

    # Update interests
    update_res = await async_client.patch(
        "/api/users/user_2", json={"interest_tags": ["JavaScript", "UI/UX Design"]}
    )
    assert update_res.status_code == 200
    updated_user = update_res.json()

    assert updated_user["id"] == initial_user["id"]
    assert updated_user["name"] == initial_user["name"]
    assert updated_user["interest_tags"] == ["JavaScript", "UI/UX Design"]
