"""Formal unit tests for the summarizer service (using mocked Anthropic client, no network calls)."""

from typing import Any, Dict, List
from unittest.mock import MagicMock, patch
import pytest
from app.services.summarizer import (
    build_claude_prompt,
    generate_digest_summary,
    generate_template_fallback_summary,
)


@pytest.fixture
def sample_items_with_details() -> List[Dict[str, Any]]:
    """Fixture providing sample joined ranked items with activity details."""
    return [
        {
            "activity_item_id": "item_01",
            "title": "Optimizing LLM Inference with PyTorch 2.4",
            "content": "We explored PyTorch 2.4 compiler optimizations for transformer models.",
            "relevance_score": 0.8055,
            "explanation_text": "because you follow AI, Machine Learning, Python",
            "rank_position": 1,
        },
        {
            "activity_item_id": "item_86",
            "title": "Fine-Tuning Whisper for Multilingual Speech Recognition",
            "content": "A detailed guide on fine-tuning OpenAI Whisper on low-resource languages.",
            "relevance_score": 0.8195,
            "explanation_text": "because you follow AI, Machine Learning, Python",
            "rank_position": 2,
        },
    ]


def test_generate_digest_summary_llm_success(sample_items_with_details):
    """Test LLM path when mocked Anthropic client returns valid prose."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_text_block = MagicMock()
    mock_text_block.text = (
        "Alice, here is your weekly digest: PyTorch 2.4 compiler optimizations and Whisper "
        "multilingual speech recognition fine-tuning highlight your top updates in AI and Python."
    )
    mock_response.content = [mock_text_block]
    mock_client.messages.create.return_value = mock_response

    summary = generate_digest_summary(
        user_name="Alice Chen",
        ranked_items_with_details=sample_items_with_details,
        use_llm=True,
        client=mock_client,
    )

    assert "Alice, here is your weekly digest" in summary
    mock_client.messages.create.assert_called_once()


def test_generate_digest_summary_use_llm_false(sample_items_with_details):
    """Test fallback path when use_llm=False."""
    summary = generate_digest_summary(
        user_name="Alice Chen",
        ranked_items_with_details=sample_items_with_details,
        use_llm=False,
    )

    assert "### Weekly Digest Summary for Alice Chen" in summary
    assert "**Optimizing LLM Inference with PyTorch 2.4**" in summary
    assert "*because you follow AI, Machine Learning, Python*" in summary


def test_generate_digest_summary_llm_exception_fallback(sample_items_with_details):
    """Test that any exception raised during LLM call gracefully triggers fallback."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = RuntimeError("API Timeout / Connection Error")

    summary = generate_digest_summary(
        user_name="Bob Smith",
        ranked_items_with_details=sample_items_with_details,
        use_llm=True,
        client=mock_client,
    )

    # Should gracefully return template fallback without raising exception
    assert "### Weekly Digest Summary for Bob Smith" in summary
    assert "**Optimizing LLM Inference with PyTorch 2.4**" in summary


def test_empty_ranked_items_edge_case():
    """Test empty items list returns default fallback string."""
    summary_llm = generate_digest_summary(
        user_name="Empty User",
        ranked_items_with_details=[],
        use_llm=True,
    )

    summary_fallback = generate_digest_summary(
        user_name="Empty User",
        ranked_items_with_details=[],
        use_llm=False,
    )

    expected = "No highly relevant updates were found for you this week."
    assert summary_llm == expected
    assert summary_fallback == expected


def test_missing_api_key_triggers_fallback(sample_items_with_details):
    """Test that missing ANTHROPIC_API_KEY triggers fallback gracefully."""
    with patch.dict("os.environ", {}, clear=True):
        summary = generate_digest_summary(
            user_name="Charlie Davis",
            ranked_items_with_details=sample_items_with_details,
            use_llm=True,
            client=None,
        )

        assert "### Weekly Digest Summary for Charlie Davis" in summary
        assert "**Optimizing LLM Inference with PyTorch 2.4**" in summary


def test_build_claude_prompt_contains_user_and_item_details(sample_items_with_details):
    """Test build_claude_prompt includes user name and item titles."""
    prompt = build_claude_prompt("Diana Prince", sample_items_with_details)

    assert "Diana Prince" in prompt
    assert "Optimizing LLM Inference with PyTorch 2.4" in prompt
    assert "Fine-Tuning Whisper for Multilingual Speech Recognition" in prompt
    assert "because you follow AI, Machine Learning, Python" in prompt
