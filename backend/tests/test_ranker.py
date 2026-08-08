"""Formal unit tests for the deterministic ranker service (pure functions with in-memory test data)."""

from datetime import datetime, timedelta, timezone
import pytest
from app.services.ranker import (
    MIN_RELEVANCE_THRESHOLD,
    RankedItem,
    compute_engagement_score,
    compute_recency_decay,
    compute_tag_match_score,
    derive_explanation,
    rank_items_for_user,
)


def test_tag_match_score_full_vs_no_overlap():
    """Test that full interest overlap yields a higher score than zero overlap."""
    user_interests = ["AI", "Python"]

    full_match_tags = ["AI", "Python"]
    no_match_tags = ["Cooking", "Gardening"]

    score_full = compute_tag_match_score(user_interests, full_match_tags)
    score_none = compute_tag_match_score(user_interests, no_match_tags)

    assert score_full == 1.0
    assert score_none == 0.0


def test_recency_decay_fresh_vs_old():
    """Test that a fresh item scores higher in recency than an old item."""
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    fresh_time = now - timedelta(hours=2)
    old_time = now - timedelta(days=10)

    recency_fresh = compute_recency_decay(fresh_time, now=now)
    recency_old = compute_recency_decay(old_time, now=now)

    assert recency_fresh > recency_old
    assert 0.0 <= recency_old < recency_fresh <= 1.0


def test_zero_category_tags_fallback_explanation():
    """Test that an item with zero category tags uses the popular item fallback explanation."""
    user = {"id": "user_1", "interest_tags": ["AI", "Python"]}
    item_no_tags = {
        "id": "item_no_tags",
        "title": "Generic Popular Item",
        "category_tags": [],
        "created_at": datetime.now(timezone.utc),
        "engagement_metadata": {"views": 1000, "likes": 50, "shares": 10},
    }

    ranked = rank_items_for_user(user, [item_no_tags], top_n=5)
    assert len(ranked) == 1
    assert ranked[0].explanation_text == "popular activity item in your network this week"


def test_empty_user_interests_no_crash():
    """Test that a user with empty interest_tags does not crash and gets tag match score 0."""
    user_empty = {"id": "user_empty", "interest_tags": []}
    item = {
        "id": "item_1",
        "category_tags": ["AI", "Python"],
        "created_at": datetime.now(timezone.utc),
        "engagement_metadata": {"views": 500, "likes": 20, "shares": 5},
    }

    score = compute_tag_match_score(user_empty["interest_tags"], item["category_tags"])
    assert score == 0.0

    ranked = rank_items_for_user(user_empty, [item], top_n=5)
    assert len(ranked) == 1
    assert ranked[0].relevance_score >= MIN_RELEVANCE_THRESHOLD


def test_sub_threshold_items_excluded():
    """Test that items scoring below MIN_RELEVANCE_THRESHOLD (0.10) are filtered out."""
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    user = {"id": "user_1", "interest_tags": ["Quantum Computing"]}

    # Item with zero tag match, 30 days old (near 0 recency), and zero engagement
    sub_threshold_item = {
        "id": "item_ancient",
        "category_tags": ["Cooking"],
        "created_at": now - timedelta(days=30),
        "engagement_metadata": {"views": 0, "likes": 0, "shares": 0},
    }

    ranked = rank_items_for_user(user, [sub_threshold_item], top_n=5, now=now)
    assert len(ranked) == 0


def test_top_n_selection_and_sorting():
    """Test that top_n returns at most N items sorted descending by relevance score."""
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    user = {"id": "user_1", "interest_tags": ["AI", "Python"]}

    items = [
        {
            "id": f"item_{i}",
            "category_tags": ["AI"] if i % 2 == 0 else ["Python", "AI"],
            "created_at": now - timedelta(hours=i),
            "engagement_metadata": {"views": i * 100, "likes": i * 5, "shares": i},
        }
        for i in range(10)
    ]

    ranked = rank_items_for_user(user, items, top_n=3, now=now)
    assert len(ranked) == 3

    # Confirm sorted descending
    scores = [r.relevance_score for r in ranked]
    assert scores == sorted(scores, reverse=True)

    # Confirm rank positions are 1, 2, 3
    positions = [r.rank_position for r in ranked]
    assert positions == [1, 2, 3]


def test_explanation_text_lists_overlapping_tags():
    """Test that matching tags explanation correctly lists the actual overlapping tags."""
    user_interests = ["AI", "Machine Learning", "Python"]
    item_tags = ["Python", "AI", "Cloud"]

    explanation = derive_explanation(set(user_interests).intersection(set(item_tags)))
    assert explanation == "because you follow AI, Python"


def test_boost_tag_new_interest_explanation_wording():
    """Test that boosting a tag not in user interests updates explanation text truthfully."""
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    user = {"id": "user_1", "interest_tags": ["AI"]}

    item_cloud = {
        "id": "item_cloud",
        "category_tags": ["Cloud"],
        "created_at": now - timedelta(hours=1),
        "engagement_metadata": {"views": 100, "likes": 10, "shares": 2},
    }
    item_mixed = {
        "id": "item_mixed",
        "category_tags": ["AI", "Cloud"],
        "created_at": now - timedelta(hours=1),
        "engagement_metadata": {"views": 100, "likes": 10, "shares": 2},
    }

    ranked = rank_items_for_user(user, [item_cloud, item_mixed], boost_tag="Cloud", now=now)
    assert len(ranked) == 2

    by_id = {r.activity_item_id: r for r in ranked}
    assert by_id["item_cloud"].explanation_text == "related to trending topic: Cloud"
    assert by_id["item_mixed"].explanation_text == "because you follow AI and related to trending topic: Cloud"


def test_boost_tag_already_in_interests_no_duplication():
    """Test that boosting a tag already in user interests does not duplicate or alter explanation structure."""
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    user = {"id": "user_1", "interest_tags": ["AI", "Python"]}

    item = {
        "id": "item_1",
        "category_tags": ["AI"],
        "created_at": now - timedelta(hours=1),
        "engagement_metadata": {"views": 100, "likes": 10, "shares": 2},
    }

    ranked_normal = rank_items_for_user(user, [item], boost_tag=None, now=now)
    ranked_boosted = rank_items_for_user(user, [item], boost_tag="AI", now=now)

    assert len(ranked_normal) == 1 and len(ranked_boosted) == 1
    assert ranked_boosted[0].explanation_text == "because you follow AI"
    assert "trending topic" not in ranked_boosted[0].explanation_text


def test_boost_tag_default_none_preserves_behavior():
    """Test that omitting boost_tag produces 100% identical output to explicit boost_tag=None."""
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    user = {"id": "user_1", "interest_tags": ["Python"]}
    items = [
        {
            "id": "item_1",
            "category_tags": ["Python"],
            "created_at": now - timedelta(hours=2),
            "engagement_metadata": {"views": 200, "likes": 20, "shares": 5},
        }
    ]

    r1 = rank_items_for_user(user, items, now=now)
    r2 = rank_items_for_user(user, items, boost_tag=None, now=now)

    assert r1[0].relevance_score == r2[0].relevance_score
    assert r1[0].explanation_text == r2[0].explanation_text


def test_diversity_boost_default_false_identical_behavior():
    """Test that diversity_boost=False produces identical output to calling rank_items_for_user with defaults."""
    user = {"id": "user_1", "interest_tags": ["AI", "Python"]}
    now = datetime(2026, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
    items = [
        {
            "id": f"item_{i}",
            "title": f"Title {i}",
            "content": "Content",
            "category_tags": ["AI"],
            "created_at": now,
            "engagement_metadata": {"views": 100, "likes": 10},
        }
        for i in range(5)
    ]
    r_default = rank_items_for_user(user, items, top_n=3, now=now)
    r_false = rank_items_for_user(user, items, top_n=3, now=now, diversity_boost=False)
    assert [i.activity_item_id for i in r_default] == [i.activity_item_id for i in r_false]


def test_diversity_boost_caps_primary_tag_at_two():
    """Test that diversity_boost=True caps primary tag at 2 items when items with alternative tags exist."""
    user = {"id": "user_1", "interest_tags": ["AI", "Security", "Python"]}
    now = datetime(2026, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
    items = [
        {
            "id": "ai_1", "title": "AI 1", "content": "c", "category_tags": ["AI"],
            "created_at": now, "engagement_metadata": {"views": 500, "likes": 50}
        },
        {
            "id": "ai_2", "title": "AI 2", "content": "c", "category_tags": ["AI"],
            "created_at": now, "engagement_metadata": {"views": 400, "likes": 40}
        },
        {
            "id": "ai_3", "title": "AI 3", "content": "c", "category_tags": ["AI"],
            "created_at": now, "engagement_metadata": {"views": 300, "likes": 30}
        },
        {
            "id": "sec_1", "title": "Sec 1", "content": "c", "category_tags": ["Security"],
            "created_at": now, "engagement_metadata": {"views": 250, "likes": 25}
        },
    ]

    # Without diversity boost, top 3 items are ai_2, ai_1, ai_3 (all AI)
    standard_res = rank_items_for_user(user, items, top_n=3, now=now, diversity_boost=False)
    assert [i.activity_item_id for i in standard_res] == ["ai_2", "ai_1", "ai_3"]

    # With diversity boost, third item selected is sec_1 instead of ai_3
    diverse_res = rank_items_for_user(user, items, top_n=3, now=now, diversity_boost=True)
    assert [i.activity_item_id for i in diverse_res] == ["ai_2", "ai_1", "sec_1"]

