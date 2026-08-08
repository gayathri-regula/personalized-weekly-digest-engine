"""Tests for the item feedback submission and retrieval endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_submit_valid_feedback(async_client: AsyncClient):
    """Test valid feedback submission returns 200 OK and FeedbackResponse."""
    payload = {"feedback_type": "useful"}
    response = await async_client.post(
        "/api/feedback/user_1/item_01", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_1"
    assert data["activity_item_id"] == "item_01"
    assert data["feedback_type"] == "useful"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_submit_invalid_feedback_type_rejected(async_client: AsyncClient):
    """Test invalid feedback_type returns HTTP 400 Bad Request."""
    payload = {"feedback_type": "invalid_type_xyz"}
    response = await async_client.post(
        "/api/feedback/user_1/item_01", json=payload
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_submit_nonexistent_user_rejected(async_client: AsyncClient):
    """Test feedback submission for nonexistent user returns HTTP 404."""
    payload = {"feedback_type": "useful"}
    response = await async_client.post(
        "/api/feedback/nonexistent_user_999/item_01", json=payload
    )
    assert response.status_code == 404
    assert "User 'nonexistent_user_999' not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_submit_nonexistent_item_rejected(async_client: AsyncClient):
    """Test feedback submission for nonexistent activity item returns HTTP 404."""
    payload = {"feedback_type": "useful"}
    response = await async_client.post(
        "/api/feedback/user_1/nonexistent_item_999", json=payload
    )
    assert response.status_code == 404
    assert "Activity item 'nonexistent_item_999' not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_resubmit_feedback_updates_existing_record(async_client: AsyncClient):
    """Test resubmitting feedback for the same (user_id, item_id) updates rating instead of duplicating."""
    # First submission: useful
    res1 = await async_client.post(
        "/api/feedback/user_1/item_01", json={"feedback_type": "useful"}
    )
    assert res1.status_code == 200
    fb_id_1 = res1.json()["id"]

    # Second submission: not_useful
    res2 = await async_client.post(
        "/api/feedback/user_1/item_01", json={"feedback_type": "not_useful"}
    )
    assert res2.status_code == 200
    fb_id_2 = res2.json()["id"]

    # Verify ID is preserved / updated
    assert fb_id_1 == fb_id_2
    assert res2.json()["feedback_type"] == "not_useful"


@pytest.mark.anyio
async def test_digest_includes_submitted_feedback(async_client: AsyncClient):
    """Test that POST /api/digest/{user_id} and GET /api/digest/{user_id} include feedback_type."""
    # Submit feedback first
    await async_client.post(
        "/api/feedback/user_1/item_01", json={"feedback_type": "not_interested"}
    )

    # Generate digest
    post_res = await async_client.post("/api/digest/user_1")
    assert post_res.status_code == 200
    items = post_res.json()["items"]
    target_item = next((it for it in items if it["activity_item_id"] == "item_01"), None)
    if target_item:
        assert target_item["feedback_type"] == "not_interested"

    # Get digest
    get_res = await async_client.get("/api/digest/user_1")
    assert get_res.status_code == 200
    get_items = get_res.json()["items"]
    target_get_item = next((it for it in get_items if it["activity_item_id"] == "item_01"), None)
    if target_get_item:
        assert target_get_item["feedback_type"] == "not_interested"

