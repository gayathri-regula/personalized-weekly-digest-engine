"""Unit tests for AI digest generator service."""

import pytest
from unittest.mock import MagicMock

from app.constants import INTEREST_TAXONOMY
from app.services.ai_digest_generator import (
    call_llm_ai_digest_generator,
    generate_ai_digest_items,
    generate_fallback_ai_digest_items,
    sanitize_category_tags,
)


def test_generate_fallback_ai_digest_items():
    """Test fallback generator returns 5 valid items with section_title and truthful explanations."""
    user_name = "Grace Hopper"
    interest_tags = ["AI", "Cloud", "Security"]

    items = generate_fallback_ai_digest_items(user_name, interest_tags)
    assert len(items) == 5

    for idx, item in enumerate(items, start=1):
        assert "title" in item and len(item["title"]) > 0
        assert "content" in item and len(item["content"]) > 0
        assert "category_tags" in item and len(item["category_tags"]) > 0
        assert isinstance(item["category_tags"][0], str) and len(item["category_tags"][0]) > 0
        assert "section_title" in item and len(item["section_title"]) > 0
        assert "explanation_text" in item and len(item["explanation_text"]) > 0
        assert "relevance_score" in item
        assert item["relevance_score"] > 0.80
        assert item["rank_position"] == idx
        assert item["engagement_metadata"].get("is_ai_generated") is True


@pytest.mark.parametrize(
    "tags",
    [
        ["AI"],  # 1 tag case
        ["AI", "Python"],  # 2 tags case
        ["AI", "Cloud", "Security"],  # 3+ tags case
        [],  # Empty user tags case
    ],
)
def test_fallback_generator_zero_duplicate_pairs_for_varying_tag_counts(tags):
    """Verify fallback generator produces 5 items with zero duplicate (title, content) pairs for 1, 2, 3+ tags."""
    items = generate_fallback_ai_digest_items("Alice Chen", tags)
    assert len(items) == 5

    pairs = [(item["title"], item["content"]) for item in items]
    unique_pairs = set(pairs)
    assert len(unique_pairs) == 5, f"Duplicate pairs detected for user tags {tags}: {pairs}"


def test_fallback_exploratory_items_positions_and_distinctness():
    """Verify items 4 and 5 in fallback mode are distinct exploratory topics."""
    user_name = "Ada Lovelace"
    interest_tags = ["AI", "Python"]

    items = generate_fallback_ai_digest_items(user_name, interest_tags)
    assert len(items) == 5

    pos4 = items[3]
    pos5 = items[4]

    # Items 4 and 5 must have rank_position 4 and 5
    assert pos4["rank_position"] == 4
    assert pos5["rank_position"] == 5

    # Items 4 and 5 must be distinct from each other
    assert (pos4["title"], pos4["content"]) != (pos5["title"], pos5["content"])

    # Items 4 and 5 must be distinct from items 1-3
    items_1_to_3_pairs = set((item["title"], item["content"]) for item in items[:3])
    assert (pos4["title"], pos4["content"]) not in items_1_to_3_pairs
    assert (pos5["title"], pos5["content"]) not in items_1_to_3_pairs

    # Check that explanation indicates exploratory nature
    assert "Exploratory update" in pos4["explanation_text"]
    assert "Exploratory update" in pos5["explanation_text"]


def test_sanitize_category_tags_guardrails():
    """Verify category tag sanitization guardrails."""
    # Valid tags preserved
    assert sanitize_category_tags(["Vector Databases", "LLM Systems"]) == ["Vector Databases", "LLM Systems"]
    # Trimming whitespace
    assert sanitize_category_tags(["  Edge AI  "]) == ["Edge AI"]
    # Invalid non-list inputs fallback to default
    assert sanitize_category_tags(None, "Technology") == ["Technology"]
    assert sanitize_category_tags("Not A List", "Technology") == ["Technology"]
    # Empty strings or invalid lengths ignored / fallback applied
    assert sanitize_category_tags([""], "Technology") == ["Technology"]
    assert sanitize_category_tags(["a"], "Technology") == ["Technology"]  # <2 chars
    assert sanitize_category_tags(["A" * 50], "Technology") == ["Technology"]  # >40 chars


def test_generate_ai_digest_items_uses_fallback_when_llm_fails():
    """Test generate_ai_digest_items falls back gracefully when LLM fails."""
    user_name = "Ada Lovelace"
    interest_tags = ["Python", "Backend Engineering"]

    items = generate_ai_digest_items(user_name, interest_tags, use_llm=False)
    assert len(items) == 5
    assert items[0]["category_tags"][0] in interest_tags
    assert "section_title" in items[0] and len(items[0]["section_title"]) > 0


def test_call_llm_ai_digest_generator_mock_success():
    """Test call_llm_ai_digest_generator with a mocked OpenAI response including section_title."""
    mock_client = MagicMock()
    mock_response = MagicMock()

    mock_json_content = """[
      {"title": "AI Title 1", "content": "AI Description 1.", "category_tags": ["AI Agents"], "section_title": "AI & Autonomous Systems", "explanation_text": "Tailored to your interest in AI"},
      {"title": "AI Title 2", "content": "AI Description 2.", "category_tags": ["Cloud Native"], "section_title": "Cloud & DevOps", "explanation_text": "Tailored to your interest in Cloud"},
      {"title": "AI Title 3", "content": "AI Description 3.", "category_tags": ["Python Async"], "section_title": "Languages & Ecosystems", "explanation_text": "Tailored to your interest in Python"},
      {"title": "AI Title 4", "content": "AI Description 4.", "category_tags": ["Quantum Hardware"], "section_title": "Quantum Computing", "explanation_text": "Exploratory update: Quantum Hardware"},
      {"title": "AI Title 5", "content": "AI Description 5.", "category_tags": ["Edge Computing"], "section_title": "Edge & Autonomous Systems", "explanation_text": "Exploratory update: Edge Computing"}
    ]"""

    mock_choice = MagicMock()
    mock_choice.message.content = mock_json_content
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    items = call_llm_ai_digest_generator(
        user_name="Alan Turing",
        interest_tags=["AI", "Security"],
        client=mock_client,
    )

    assert len(items) == 5
    assert items[0]["title"] == "AI Title 1"
    assert items[0]["category_tags"] == ["AI Agents"]
    assert items[0]["section_title"] == "AI & Autonomous Systems"
    assert items[0]["explanation_text"] == "Tailored to your interest in AI"
    assert items[0]["relevance_score"] == 0.95
    assert items[4]["rank_position"] == 5
    assert items[4]["section_title"] == "Edge & Autonomous Systems"


def test_build_ai_digest_prompt_representative_spread_instruction():
    """Verify build_ai_digest_prompt includes specific representative spread instruction when tag count > 3."""
    from app.services.ai_digest_generator import build_ai_digest_prompt

    # <= 3 tags case
    prompt_small = build_ai_digest_prompt("Bob", ["AI", "Python"])
    assert "Generate updates directly tailored to Bob's followed interest topics." in prompt_small

    # > 3 tags case (e.g. 5 tags)
    tags_5 = ["AI", "Machine Learning", "Python", "Cloud", "Security"]
    prompt_large = build_ai_digest_prompt("Alice", tags_5)
    assert "representative, diverse spread across Alice's 5 followed interest topics" in prompt_large
    assert "Do NOT limit items 1-3 to only the first few tags" in prompt_large


@pytest.mark.parametrize(
    "tags",
    [
        ["AI", "Machine Learning", "Python", "JavaScript", "Cloud"],  # 5 tags
        ["AI", "Machine Learning", "Python", "JavaScript", "Cloud", "DevOps", "Data Science", "Security"],  # 8 tags
        INTEREST_TAXONOMY,  # 12 tags (all taxonomy tags)
    ],
)
def test_fallback_generator_many_tags_sampling_spread(tags):
    """Verify fallback generator samples across the full tag list for >3 tags and maintains 0 duplicates."""
    items = generate_fallback_ai_digest_items("Dana", tags)
    assert len(items) == 5

    # Check zero duplicate pairs
    pairs = [(item["title"], item["content"]) for item in items]
    assert len(set(pairs)) == 5

    # Items 1-3 tags
    tailored_tags = [items[0]["category_tags"][0], items[1]["category_tags"][0], items[2]["category_tags"][0]]
    # Ensure all tailored tags are in the user's tag list
    for t in tailored_tags:
        assert t in tags

    # For 5+ tags, verify item 3's tag is NOT limited to tags[0..2]
    # e.g. for 5 tags (idx 2 * 5 // 3 = 3), item 3 tag is tags[3] ("JavaScript")
    # for 12 tags (idx 2 * 12 // 3 = 8), item 3 tag is tags[8] ("Security")
    first_3_user_tags = tags[:3]
    has_tag_beyond_first_3 = any(t not in first_3_user_tags for t in tailored_tags)
    assert has_tag_beyond_first_3, f"Tailored tags {tailored_tags} did not sample beyond first 3 user tags {first_3_user_tags}"


@pytest.mark.parametrize(
    "tags",
    [
        ["AI"],  # 1 tag case
        ["AI", "Python"],  # 2 tags case
        ["AI", "Cloud", "Security"],  # 3 tags case
        ["AI", "Machine Learning", "Python", "JavaScript", "Cloud"],  # 5 tags case
        [],  # Empty tag case
    ],
)
def test_fallback_generator_3_items_zero_duplicate_pairs(tags):
    """Verify 3-item fallback mode returns 3 items with 2 interest + 1 exploratory and 0 duplicate pairs."""
    items = generate_fallback_ai_digest_items("Alice Chen", tags, target_count=3)
    assert len(items) == 3

    # Check position rankings
    for idx, item in enumerate(items, start=1):
        assert item["rank_position"] == idx

    # Check zero duplicate (title, content) pairs across all 3 items
    pairs = [(item["title"], item["content"]) for item in items]
    unique_pairs = set(pairs)
    assert len(unique_pairs) == 3, f"Duplicate pairs detected in 3-item mode for tags {tags}: {pairs}"

    # Item 3 must be exploratory
    assert "Exploratory update" in items[2]["explanation_text"]



