"""Tests for the saved items and user activity log endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_save_and_unsave_item(async_client: AsyncClient):
    """Test saving an item, listing saved items, and unsaving it."""
    # 1. Save item_01 for user_1
    save_res = await async_client.post("/api/saved/user_1/item_01")
    assert save_res.status_code == 201
    save_data = save_res.json()
    assert save_data["user_id"] == "user_1"
    assert save_data["activity_item_id"] == "item_01"

    # 2. List saved items for user_1
    list_res = await async_client.get("/api/saved/user_1")
    assert list_res.status_code == 200
    saved_items = list_res.json()
    assert len(saved_items) >= 1
    assert any(it["activity_item_id"] == "item_01" for it in saved_items)

    # 3. Unsave item_01 for user_1
    del_res = await async_client.delete("/api/saved/user_1/item_01")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # 4. Verify list no longer contains item_01
    list_res_after = await async_client.get("/api/saved/user_1")
    assert list_res_after.status_code == 200
    assert not any(it["activity_item_id"] == "item_01" for it in list_res_after.json())


@pytest.mark.anyio
async def test_activity_log_records_events(async_client: AsyncClient):
    """Test that performing user actions creates entries in the user activity log."""
    # Submit feedback to trigger activity log hook
    await async_client.post("/api/feedback/user_1/item_02", json={"feedback_type": "useful"})

    # Fetch activity log for user_1
    act_res = await async_client.get("/api/activity/user_1?limit=10")
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert "items" in act_data
    assert "total" in act_data
    assert act_data["total"] >= 1
    assert any(item["event_type"] == "feedback_submitted" for item in act_data["items"])
