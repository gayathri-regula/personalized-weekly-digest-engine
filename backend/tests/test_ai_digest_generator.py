"""Unit tests for AI digest generator service."""

import pytest
from unittest.mock import MagicMock

from app.constants import INTEREST_TAXONOMY
from app.services.ai_digest_generator import (
    generate_ai_digest_items,
    generate_fallback_ai_digest_items,
    call_llm_ai_digest_generator,
)


def test_generate_fallback_ai_digest_items():
    """Test deterministic fallback generator returns 5 valid items."""
    user_name = "Grace Hopper"
    interest_tags = ["AI", "Cloud", "Security"]

    items = generate_fallback_ai_digest_items(user_name, interest_tags)
    assert len(items) == 5

    for idx, item in enumerate(items, start=1):
        assert "title" in item and len(item["title"]) > 0
        assert "content" in item and len(item["content"]) > 0
        assert "category_tags" in item and len(item["category_tags"]) > 0
        assert item["category_tags"][0] in INTEREST_TAXONOMY
        assert "explanation_text" in item
        assert item["explanation_text"].startswith("AI-generated highlight tailored")
        assert "relevance_score" in item
        assert item["relevance_score"] > 0.80
        assert item["rank_position"] == idx
        assert item["engagement_metadata"].get("is_ai_generated") is True


@pytest.mark.parametrize(
    "tags, expected_unique_count",
    [
        (["AI"], 3),  # 1 tag with 3 variants available -> 3 unique items out of 5
        (["AI", "Python"], 5),  # 2 tags with 3 variants each -> 5 unique items out of 5
        (["AI", "Machine Learning", "Python"], 5),  # 3 tags (Alice Chen case) -> 5 unique items out of 5
    ],
)
def test_generate_fallback_ai_digest_items_no_duplicates_for_few_tags(
    tags, expected_unique_count
):
    """Assert fallback generator produces unique (title, content) pairs without premature duplication."""
    items = generate_fallback_ai_digest_items("Alice Chen", tags)
    assert len(items) == 5

    pairs = [(item["title"], item["content"]) for item in items]
    unique_pairs = set(pairs)
    assert len(unique_pairs) == expected_unique_count

    # Verify no duplicate pair appears before all variants for that tag are exhausted
    first_n_items = pairs[:expected_unique_count]
    assert len(set(first_n_items)) == expected_unique_count



def test_generate_ai_digest_items_uses_fallback_when_llm_fails():
    """Test generate_ai_digest_items falls back gracefully when LLM fails."""
    user_name = "Ada Lovelace"
    interest_tags = ["Python", "Backend Engineering"]

    # Passing use_llm=True with invalid/empty client triggers warning and returns fallback
    items = generate_ai_digest_items(user_name, interest_tags, use_llm=False)
    assert len(items) == 5
    assert items[0]["category_tags"][0] in interest_tags


def test_call_llm_ai_digest_generator_mock_success():
    """Test call_llm_ai_digest_generator with a mocked Anthropic response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    
    mock_json_content = """[
      {"title": "AI Title 1", "content": "AI Description 1.", "category_tags": ["AI"], "explanation_text": "AI Explanation 1"},
      {"title": "AI Title 2", "content": "AI Description 2.", "category_tags": ["Cloud"], "explanation_text": "AI Explanation 2"},
      {"title": "AI Title 3", "content": "AI Description 3.", "category_tags": ["Python"], "explanation_text": "AI Explanation 3"},
      {"title": "AI Title 4", "content": "AI Description 4.", "category_tags": ["DevOps"], "explanation_text": "AI Explanation 4"},
      {"title": "AI Title 5", "content": "AI Description 5.", "category_tags": ["Security"], "explanation_text": "AI Explanation 5"}
    ]"""

    mock_block = MagicMock()
    mock_block.text = mock_json_content
    mock_response.content = [mock_block]
    mock_client.messages.create.return_value = mock_response

    items = call_llm_ai_digest_generator(
        user_name="Alan Turing",
        interest_tags=["AI", "Security"],
        client=mock_client,
    )

    assert len(items) == 5
    assert items[0]["title"] == "AI Title 1"
    assert items[0]["category_tags"] == ["AI"]
    assert items[0]["explanation_text"] == "AI Explanation 1"
    assert items[0]["relevance_score"] == 0.95
    assert items[4]["rank_position"] == 5
