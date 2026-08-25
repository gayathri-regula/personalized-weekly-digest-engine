"""Tests for Voice Digest TTS endpoints and service logic using OpenAI TTS."""

from unittest.mock import MagicMock
import pytest
from httpx import AsyncClient

from app.services.voice_generator import generate_voice_digest


def test_generate_voice_digest_empty_prose():
    """Test generate_voice_digest raises ValueError when summary prose is empty."""
    with pytest.raises(ValueError, match="Summary prose text cannot be empty"):
        generate_voice_digest("")

    with pytest.raises(ValueError, match="Summary prose text cannot be empty"):
        generate_voice_digest("   ")


def test_generate_voice_digest_missing_api_key(monkeypatch):
    """Test generate_voice_digest raises ValueError when OPENAI_API_KEY is missing."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is missing or empty"):
        generate_voice_digest("Valid summary prose.")


def test_generate_voice_digest_mock_client_success():
    """Test generate_voice_digest with mocked OpenAI client returns audio bytes."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    fake_audio_bytes = b"fake_mp3_audio_stream_data"
    mock_response.content = fake_audio_bytes
    mock_client.audio.speech.create.return_value = mock_response

    result = generate_voice_digest(
        summary_prose="Welcome to your weekly digest summary.",
        voice="alloy",
        client=mock_client,
    )

    assert result == fake_audio_bytes
    mock_client.audio.speech.create.assert_called_once_with(
        model="tts-1",
        voice="alloy",
        input="Welcome to your weekly digest summary.",
        response_format="mp3",
    )


def test_generate_voice_digest_truncation_safeguard():
    """Test long summary prose exceeding 4000 characters is truncated."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = b"fake_audio"
    mock_client.audio.speech.create.return_value = mock_response

    long_prose = "A" * 5000
    generate_voice_digest(long_prose, client=mock_client)

    call_args = mock_client.audio.speech.create.call_args
    assert len(call_args.kwargs["input"]) == 4000


@pytest.mark.anyio
async def test_get_voice_user_not_found(async_client: AsyncClient):
    """Test GET /api/digest/{user_id}/voice returns 404 when user does not exist."""
    res = await async_client.get("/api/digest/non_existent_user/voice")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.anyio
async def test_get_voice_no_digest(async_client: AsyncClient):
    """Test GET /api/digest/{user_id}/voice returns 404 when user has no digest generated."""
    res = await async_client.get("/api/digest/user_2/voice")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data
    assert "no digest found" in data["detail"].lower()


@pytest.mark.anyio
async def test_get_voice_missing_api_key(async_client: AsyncClient, monkeypatch):
    """Test GET /api/digest/{user_id}/voice returns 502 when OPENAI_API_KEY is missing."""
    gen_res = await async_client.post("/api/digest/user_1")
    assert gen_res.status_code == 200

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    res = await async_client.get("/api/digest/user_1/voice")
    assert res.status_code == 502
    data = res.json()
    assert "openai_api_key" in data["detail"].lower()


@pytest.mark.anyio
async def test_get_voice_success_mocked(async_client: AsyncClient, monkeypatch):
    """Test GET /api/digest/{user_id}/voice returns 200 audio content when TTS call succeeds."""
    gen_res = await async_client.post("/api/digest/user_1")
    assert gen_res.status_code == 200

    fake_mp3 = b"fake_mp3_stream_content"

    def fake_generate(summary_prose: str, voice: str = "alloy"):
        return fake_mp3

    monkeypatch.setattr("app.routers.digest.generate_voice_digest", fake_generate)

    res = await async_client.get("/api/digest/user_1/voice")
    assert res.status_code == 200
    assert res.content == fake_mp3
