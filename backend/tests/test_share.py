"""Tests for Share Your Digest backend endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_generate_share_link(async_client: AsyncClient):
    """Test generating a share link for an existing user."""
    res = await async_client.post("/api/users/user_1/share")
    assert res.status_code == 200
    data = res.json()
    assert "share_token" in data
    assert "share_url" in data
    token = data["share_token"]
    assert len(token) > 10
    assert token in data["share_url"]

    # Test idempotency - calling again returns exact same share token
    res2 = await async_client.post("/api/users/user_1/share")
    assert res2.status_code == 200
    assert res2.json()["share_token"] == token


@pytest.mark.anyio
async def test_generate_share_link_user_not_found(async_client: AsyncClient):
    """Test share link generation for non-existent user."""
    res = await async_client.post("/api/users/non_existent_user/share")
    assert res.status_code == 404


@pytest.mark.anyio
async def test_get_shared_digest_invalid_token(async_client: AsyncClient):
    """Test retrieving shared digest with invalid token."""
    res = await async_client.get("/api/share/invalid_token_12345")
    assert res.status_code == 404


@pytest.mark.anyio
async def test_get_shared_digest_success(async_client: AsyncClient):
    """Test generating a digest and retrieving it via public share link."""
    # 1. Generate digest for user_1
    gen_res = await async_client.post("/api/digest/user_1")
    assert gen_res.status_code == 200

    # 2. Get share link
    share_res = await async_client.post("/api/users/user_1/share")
    assert share_res.status_code == 200
    token = share_res.json()["share_token"]

    # 3. Retrieve shared digest publicly
    public_res = await async_client.get(f"/api/share/{token}")
    assert public_res.status_code == 200
    shared_data = public_res.json()

    assert shared_data["user_name"] == "Test User 1"
    assert "week_identifier" in shared_data
    assert "summary_prose" in shared_data
    assert len(shared_data["items"]) > 0

    # Ensure no internal user_id or feedback state is exposed on the public item object
    item = shared_data["items"][0]
    assert "user_id" not in item
    assert "feedback_type" not in item
    assert "title" in item
    assert "content" in item
