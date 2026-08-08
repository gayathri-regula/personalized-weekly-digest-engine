"""Rule-based deterministic ranking engine and explanation generator.

Calculates relevance scores for activity items relative to a user's interests,
recency, and engagement signals, producing ranked recommendations with truthful
explanations without external API or LLM dependencies.
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple
from pydantic import BaseModel, Field

# Weights for relevance score formula per ARCHITECTURE.md Section 3.1
TAG_WEIGHT: float = 0.60  # Weight for interest-tag match score
RECENCY_WEIGHT: float = 0.25  # Weight for recency decay score
ENGAGEMENT_WEIGHT: float = 0.15  # Weight for normalized engagement score

# Minimum score threshold per ARCHITECTURE.md Section 10.1
MIN_RELEVANCE_THRESHOLD: float = 0.10

# Recency decay exponential lambda rate.
# A lambda of 0.20 means an item 7 days old retains exp(-0.20 * 7) ~= 0.2466 (24.7%)
# of its recency score, offering meaningful but reduced relevance after one week.
RECENCY_LAMBDA: float = 0.20


class RankedItem(BaseModel):
    """Output data structure representing a ranked activity item for a user digest."""

    activity_item_id: str = Field(
        ..., description="Unique ID of the activity item"
    )
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Computed relevance score (0.0 to 1.0)"
    )
    explanation_text: str = Field(
        ..., description="Truthful explanation text for why this item was selected"
    )
    rank_position: int = Field(
        ..., ge=1, description="1-indexed rank position in the user digest"
    )


def compute_tag_match_score(
    user_interests: Sequence[str] | None, item_tags: Sequence[str] | None
) -> float:
    """Compute the tag match score between user interests and item category tags.

    Formula: |UserInterests ∩ ItemTags| / max(1, |UserInterests|)

    Args:
        user_interests: List of interest tags specified by the user.
        item_tags: List of category tags associated with the activity item.

    Returns:
        float: Normalized tag match score between 0.0 and 1.0.
    """
    user_set = set(user_interests or [])
    item_set = set(item_tags or [])

    if not user_set:
        return 0.0

    matching = user_set.intersection(item_set)
    score = len(matching) / max(1, len(user_set))
    return min(1.0, max(0.0, float(score)))


def compute_recency_decay(
    item_created_at: datetime, now: datetime | None = None
) -> float:
    """Compute exponential recency decay score based on item age in days.

    Formula: exp(-lambda * t_days)

    Args:
        item_created_at: Datetime when the item was created.
        now: Reference datetime for scoring. Defaults to current UTC time.

    Returns:
        float: Recency decay multiplier between 0.0 and 1.0.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Normalize timezones to ensure accurate subtraction
    if item_created_at.tzinfo is None:
        item_created_at = item_created_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    delta_seconds = (now - item_created_at).total_seconds()
    t_days = max(0.0, delta_seconds / 86400.0)

    score = math.exp(-RECENCY_LAMBDA * t_days)
    return min(1.0, max(0.0, float(score)))


def compute_engagement_score(
    engagement_metadata: Dict[str, Any] | None
) -> float:
    """Compute normalized engagement score from engagement metrics.

    Formula: min(1.0, (likes * 2 + views * 0.1 + shares * 5) / 100)

    Args:
        engagement_metadata: Dict containing 'likes', 'views', 'shares', etc.

    Returns:
        float: Normalized engagement score between 0.0 and 1.0.
    """
    if not engagement_metadata:
        return 0.0

    likes = float(engagement_metadata.get("likes", 0))
    views = float(engagement_metadata.get("views", 0))
    shares = float(engagement_metadata.get("shares", 0))

    raw_score = (likes * 2.0 + views * 0.1 + shares * 5.0) / 100.0
    return min(1.0, max(0.0, float(raw_score)))


def derive_explanation(matching_tags: Sequence[str]) -> str:
    """Derive truthful explanation text based on matching interest/category tags.

    Args:
        matching_tags: Sequence of overlapping tags between user and item.

    Returns:
        str: Human-readable explanation string.
    """
    sorted_tags = sorted(list(matching_tags))
    if sorted_tags:
        joined_tags = ", ".join(sorted_tags)
        return f"because you follow {joined_tags}"
    return "popular activity item in your network this week"


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to extract attribute from ORM object, Pydantic model, or dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def rank_items_for_user(
    user: Any,
    items: Sequence[Any],
    top_n: int = 5,
    now: datetime | None = None,
    boost_tag: Optional[str] = None,
    diversity_boost: bool = False,
) -> List[RankedItem]:
    """Score and rank activity items for a user deterministically.

    Args:
        user: User entity (ORM model instance or dict/object with interest_tags).
        items: List of ActivityItem entities to score.
        top_n: Maximum number of top items to return (default 5).
        now: Optional reference scoring time.
        boost_tag: Optional taxonomy tag string to temporarily boost matching items.
        diversity_boost: If True, post-process top_n selection to avoid selecting
            more than 2 items sharing the exact same primary category tag when alternatives exist.

    Returns:
        List[RankedItem]: Ranked items sorted descending by relevance_score,
            filtered to clear the MIN_RELEVANCE_THRESHOLD (0.10).
    """
    if now is None:
        now = datetime.now(timezone.utc)

    user_interests = _get_attr(user, "interest_tags", []) or []
    real_interests_set = set(user_interests)

    if boost_tag:
        effective_interests = list(real_interests_set | {boost_tag})
    else:
        effective_interests = list(user_interests)

    scored_items: List[Tuple[float, str, datetime, str, str, str]] = []

    for item in items:
        item_id = str(_get_attr(item, "id"))
        item_tags = _get_attr(item, "category_tags", []) or []
        item_tags_set = set(item_tags)
        primary_tag = item_tags[0] if item_tags else ""
        created_at = _get_attr(item, "created_at")
        engagement = _get_attr(item, "engagement_metadata", {}) or {}

        # Determine real overlapping tags (from saved user interest tags only)
        real_matching_set = real_interests_set.intersection(item_tags_set)
        real_matching_tags = sorted(list(real_matching_set))

        # Compute individual score components using effective tag set
        tag_score = compute_tag_match_score(effective_interests, item_tags)
        recency_score = compute_recency_decay(created_at, now=now)
        engagement_score = compute_engagement_score(engagement)

        # Weighted total relevance score
        total_score = (
            TAG_WEIGHT * tag_score
            + RECENCY_WEIGHT * recency_score
            + ENGAGEMENT_WEIGHT * engagement_score
        )
        bounded_score = round(min(1.0, max(0.0, float(total_score))), 4)

        # Exclude sub-threshold items
        if bounded_score < MIN_RELEVANCE_THRESHOLD:
            continue

        # Explanation logic for boost_tag vs standard user interests
        boost_matched_new = bool(
            boost_tag
            and (boost_tag in item_tags_set)
            and (boost_tag not in real_interests_set)
        )

        if boost_matched_new:
            if real_matching_tags:
                joined_real = ", ".join(real_matching_tags)
                explanation = (
                    f"because you follow {joined_real} and related to trending topic: {boost_tag}"
                )
            else:
                explanation = f"related to trending topic: {boost_tag}"
        else:
            explanation = derive_explanation(real_matching_tags)

        scored_items.append(
            (bounded_score, item_id, created_at, explanation, item_id, primary_tag)
        )

    # Sort descending by relevance score; use created_at and item_id as tie-breakers
    scored_items.sort(key=lambda x: (x[0], x[2], x[1]), reverse=True)

    # Select top_n items
    if diversity_boost:
        top_items = []
        tag_counts: Dict[str, int] = {}
        skipped_items = []
        for entry in scored_items:
            ptag = entry[5]
            current_count = tag_counts.get(ptag, 0) if ptag else 0
            if ptag and current_count >= 2:
                skipped_items.append(entry)
            else:
                top_items.append(entry)
                if ptag:
                    tag_counts[ptag] = current_count + 1
                if len(top_items) == top_n:
                    break
        if len(top_items) < top_n:
            for entry in skipped_items:
                top_items.append(entry)
                if len(top_items) == top_n:
                    break
    else:
        top_items = scored_items[:top_n]

    results: List[RankedItem] = []
    for rank_idx, (score, item_id, _, explanation, _, _) in enumerate(top_items, start=1):
        results.append(
            RankedItem(
                activity_item_id=item_id,
                relevance_score=score,
                explanation_text=explanation,
                rank_position=rank_idx,
            )
        )

    return results
