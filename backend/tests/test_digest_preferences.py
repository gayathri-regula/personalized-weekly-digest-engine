"""Unit tests for user digest preferences endpoint and 3-item digest generation path."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_update_user_preferences_valid(async_client: AsyncClient):
    """Test updating user digest preferences with valid values."""
    payload = {
        "digest_frequency": "daily",
        "content_length": "brief",
        "digest_language": "en",
    }
    response = await async_client.patch("/api/users/user_1/preferences", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "user_1"
    assert data["digest_frequency"] == "daily"
    assert data["content_length"] == "brief"
    assert data["digest_language"] == "en"


@pytest.mark.anyio
async def test_update_user_preferences_partial(async_client: AsyncClient):
    """Test updating only a subset of preferences preserves remaining fields."""
    # First set explicit preferences
    await async_client.patch(
        "/api/users/user_1/preferences",
        json={"digest_frequency": "monthly", "content_length": "brief"},
    )

    # Update only frequency
    response = await async_client.patch(
        "/api/users/user_1/preferences", json={"digest_frequency": "weekly"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["digest_frequency"] == "weekly"
    assert data["content_length"] == "brief"  # Preserved from previous update
    assert data["digest_language"] == "en"


@pytest.mark.anyio
async def test_update_user_preferences_invalid_frequency(async_client: AsyncClient):
    """Test updating with invalid digest frequency returns 400 Bad Request."""
    payload = {"digest_frequency": "hourly"}
    response = await async_client.patch("/api/users/user_1/preferences", json=payload)
    assert response.status_code == 400
    assert "Invalid digest frequency 'hourly'" in response.json()["detail"]


@pytest.mark.anyio
async def test_update_user_preferences_invalid_content_length(async_client: AsyncClient):
    """Test updating with invalid content length returns 400 Bad Request."""
    payload = {"content_length": "super_long"}
    response = await async_client.patch("/api/users/user_1/preferences", json=payload)
    assert response.status_code == 400
    assert "Invalid content length 'super_long'" in response.json()["detail"]


@pytest.mark.anyio
async def test_update_user_preferences_invalid_language(async_client: AsyncClient):
    """Test updating with invalid language code returns 400 Bad Request."""
    payload = {"digest_language": "fr"}
    response = await async_client.patch("/api/users/user_1/preferences", json=payload)
    assert response.status_code == 400
    assert "Invalid digest language 'fr'" in response.json()["detail"]


@pytest.mark.anyio
async def test_update_user_preferences_nonexistent_user(async_client: AsyncClient):
    """Test updating preferences for non-existent user returns 404 Not Found."""
    payload = {"content_length": "brief"}
    response = await async_client.patch("/api/users/user_99999/preferences", json=payload)
    assert response.status_code == 404
    assert "User 'user_99999' not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_digest_generation_honors_brief_content_length(async_client: AsyncClient):
    """Test that setting content_length='brief' causes POST /api/digest/{user_id} to return 3 items."""
    # Set preference to brief
    pref_res = await async_client.patch(
        "/api/users/user_1/preferences", json={"content_length": "brief"}
    )
    assert pref_res.status_code == 200

    # Generate digest
    digest_res = await async_client.post("/api/users_1" if False else "/api/digest/user_1")
    assert digest_res.status_code == 200
    digest_data = digest_res.json()

    assert len(digest_data["items"]) == 3
    for idx, item in enumerate(digest_data["items"], start=1):
        assert item["rank_position"] == idx

    # Reset preference back to detailed
    await async_client.patch(
        "/api/users/user_1/preferences", json={"content_length": "detailed"}
    )
    detailed_res = await async_client.post("/api/digest/user_1")
    assert detailed_res.status_code == 200
    assert len(detailed_res.json()["items"]) == 5
