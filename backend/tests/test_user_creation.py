"""Tests for user onboarding taxonomy and user creation endpoints."""

import pytest
from httpx import AsyncClient
from app.constants import INTEREST_TAXONOMY


@pytest.mark.anyio
async def test_get_interests_endpoint(async_client: AsyncClient):
    """Test GET /api/interests returns the complete 12-item taxonomy list."""
    response = await async_client.get("/api/interests")
    assert response.status_code == 200
    data = response.json()
    assert "interests" in data
    assert len(data["interests"]) == 12
    assert data["interests"] == INTEREST_TAXONOMY


@pytest.mark.anyio
async def test_create_user_valid(async_client: AsyncClient):
    """Test valid user creation with 3 valid interest tags."""
    payload = {
        "name": "Sarah Connor",
        "interest_tags": ["AI", "Security", "Backend Engineering"],
    }
    response = await async_client.post("/api/users", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Sarah Connor"
    assert data["interest_tags"] == ["AI", "Security", "Backend Engineering"]
    assert data["id"].startswith("user_")
    assert len(data["id"]) == 13  # "user_" (5 chars) + 8 hex chars


@pytest.mark.anyio
async def test_create_user_missing_or_empty_name(async_client: AsyncClient):
    """Test that missing or empty name is rejected with 422 status code."""
    # Empty string name
    payload_empty = {"name": "", "interest_tags": ["AI", "Python"]}
    res1 = await async_client.post("/api/users", json=payload_empty)
    assert res1.status_code == 422

    # Whitespace only name
    payload_ws = {"name": "   ", "interest_tags": ["AI", "Python"]}
    res2 = await async_client.post("/api/users", json=payload_ws)
    assert res2.status_code == 422

    # Missing name field
    payload_missing = {"interest_tags": ["AI", "Python"]}
    res3 = await async_client.post("/api/users", json=payload_missing)
    assert res3.status_code == 422


@pytest.mark.anyio
async def test_create_user_tag_count_validation(async_client: AsyncClient):
    """Test that < 2 tags is rejected with 422, while 5+ tags succeed with 201 status code."""
    # 1 tag (too few)
    payload_few = {"name": "Alex Mercer", "interest_tags": ["AI"]}
    res1 = await async_client.post("/api/users", json=payload_few)
    assert res1.status_code == 422

    # 5 tags (now valid, no upper cap)
    tags_5 = ["AI", "Machine Learning", "Python", "JavaScript", "Cloud"]
    payload_5 = {
        "name": "Alex Mercer 5",
        "interest_tags": tags_5,
    }
    res2 = await async_client.post("/api/users", json=payload_5)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["interest_tags"] == tags_5

    # 12 tags (all taxonomy tags, valid)
    payload_all = {
        "name": "Alex Mercer All",
        "interest_tags": INTEREST_TAXONOMY,
    }
    res3 = await async_client.post("/api/users", json=payload_all)
    assert res3.status_code == 201
    data3 = res3.json()
    assert data3["interest_tags"] == INTEREST_TAXONOMY


@pytest.mark.anyio
async def test_create_user_unknown_tag(async_client: AsyncClient):
    """Test that unknown interest tag is rejected with 400 status code and clear error message."""
    payload = {"name": "Invalid User", "interest_tags": ["AI", "QuantumComputing"]}
    response = await async_client.post("/api/users", json=payload)
    assert response.status_code == 400
    assert "Invalid interest tag 'QuantumComputing'" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_user_duplicate_tags(async_client: AsyncClient):
    """Test that duplicate interest tags in request are rejected with 400 status code."""
    payload = {"name": "Duplicate User", "interest_tags": ["AI", "AI", "Python"]}
    response = await async_client.post("/api/users", json=payload)
    assert response.status_code == 400
    assert "Duplicate interest tags" in response.json()["detail"]
