"""Unit tests for AI Suggestions service."""

from unittest.mock import MagicMock
import pytest

from app.services.ai_suggestions import (
    build_ai_suggestions_prompt,
    generate_ai_suggestions,
    generate_fallback_ai_suggestions,
)


def test_build_ai_suggestions_prompt():
    prompt = build_ai_suggestions_prompt("Alice", ["Python", "AI"])
    assert "Alice" in prompt
    assert "Python, AI" in prompt
    assert "EXACTLY 3" in prompt


def test_generate_fallback_ai_suggestions():
    suggestions = generate_fallback_ai_suggestions(["Backend Engineering", "DevOps"])
    assert isinstance(suggestions, list)
    assert len(suggestions) == 3
    for s in suggestions:
        assert "title" in s
        assert "description" in s
        assert "related_tag" in s
        assert len(s["title"]) > 0
        assert len(s["description"]) > 0
        assert s["related_tag"] in ["Backend Engineering", "DevOps"]


def test_generate_ai_suggestions_use_llm_false():
    suggestions = generate_ai_suggestions("Bob", ["Cloud"], use_llm=False)
    assert len(suggestions) == 3
    for s in suggestions:
        assert "title" in s
        assert "description" in s
        assert "related_tag" in s


def test_generate_ai_suggestions_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    suggestions = generate_ai_suggestions("Charlie", ["Security"], use_llm=True)
    assert len(suggestions) == 3
    for s in suggestions:
        assert "title" in s
        assert "description" in s
        assert "related_tag" in s


def test_generate_ai_suggestions_llm_success_mocked():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        '[\n'
        '  {"title": "Idea 1", "description": "Desc 1", "related_tag": "UI/UX Design"},\n'
        '  {"title": "Idea 2", "description": "Desc 2", "related_tag": "Cloud"},\n'
        '  {"title": "Idea 3", "description": "Desc 3", "related_tag": "Security"}\n'
        ']'
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    suggestions = generate_ai_suggestions(
        "Diana", ["UI/UX Design"], use_llm=True, client=mock_client
    )
    assert len(suggestions) == 3
    assert suggestions[0]["title"] == "Idea 1"
    assert suggestions[0]["description"] == "Desc 1"
    assert suggestions[0]["related_tag"] == "UI/UX Design"
    assert suggestions[1]["title"] == "Idea 2"
    assert suggestions[2]["title"] == "Idea 3"


def test_generate_ai_suggestions_llm_exception_fallback():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("API Rate Limit")

    suggestions = generate_ai_suggestions(
        "Ethan", ["Open Source"], use_llm=True, client=mock_client
    )
    assert len(suggestions) == 3
    for s in suggestions:
        assert "title" in s
        assert "description" in s
        assert "related_tag" in s
