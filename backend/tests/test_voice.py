"""Tests for Voice Digest TTS endpoints and service logic."""

import io
import wave
from unittest.mock import MagicMock
import pytest
from httpx import AsyncClient
from app.services.voice_generator import chunk_text, stitch_wav_chunks


def _create_synthetic_wav(
    frames_count: int = 100,
    nchannels: int = 1,
    sampwidth: int = 2,
    framerate: int = 16000,
) -> bytes:
    """Helper to construct synthetic WAV bytes for testing."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(nchannels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(framerate)
        raw_data = b"\x00\x00" * frames_count * nchannels
        wav_file.writeframes(raw_data)
    return buf.getvalue()


@pytest.mark.anyio
async def test_chunk_text_isolation():
    """Test text chunking helper splits long strings into <=200 char chunks without cutting words mid-word."""
    long_text = (
        "Welcome to your personalized weekly digest. "
        "This is sentence one, which provides key highlights on Artificial Intelligence and Machine Learning. "
        "This is sentence two, which covers deep insights on Cloud Architecture, Kubernetes deployment, and infrastructure optimization. "
        "Finally, sentence three details Security best practices for microservices and API access controls."
    )

    assert len(long_text) > 200

    chunks = chunk_text(long_text, max_chars=200)

    assert len(chunks) > 1

    # Verify every chunk obeys hard 200 character limit
    for chunk in chunks:
        assert len(chunk) <= 200
        assert len(chunk.strip()) > 0

    # Reassembled text should contain all original words
    reassembled = " ".join(chunks)
    assert "personalized weekly digest" in reassembled
    assert "sentence three" in reassembled

    # Test single long sentence exceeding 200 chars without sentence punctuation
    long_single = "word " * 60  # 300 characters
    chunks_single = chunk_text(long_single, max_chars=200)
    assert len(chunks_single) >= 2
    for c in chunks_single:
        assert len(c) <= 200
        for w in c.split():
            assert w == "word"


@pytest.mark.anyio
async def test_stitch_wav_chunks():
    """Test WAV stitching helper accurately concatenates PCM frames and validates audio params."""
    chunk1 = _create_synthetic_wav(frames_count=50, nchannels=1, sampwidth=2, framerate=16000)
    chunk2 = _create_synthetic_wav(frames_count=100, nchannels=1, sampwidth=2, framerate=16000)
    chunk3 = _create_synthetic_wav(frames_count=150, nchannels=1, sampwidth=2, framerate=16000)

    stitched_bytes = stitch_wav_chunks([chunk1, chunk2, chunk3])

    # Assert (a) result is valid WAV bytes (openable via wave)
    with wave.open(io.BytesIO(stitched_bytes), "rb") as wav_in:
        # Assert (b) combined frame count equals sum of input frame counts (50 + 100 + 150 = 300)
        assert wav_in.getnframes() == 300
        # Assert (c) audio parameters match
        assert wav_in.getnchannels() == 1
        assert wav_in.getsampwidth() == 2
        assert wav_in.getframerate() == 16000

    # Test parameter mismatch handling
    mismatched_chunk = _create_synthetic_wav(frames_count=50, nchannels=1, sampwidth=2, framerate=24000)
    with pytest.raises(RuntimeError, match="Incompatible WAV audio parameters"):
        stitch_wav_chunks([chunk1, mismatched_chunk])


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
    # user_2 is seeded without a digest in conftest.py
    res = await async_client.get("/api/digest/user_2/voice")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data
    assert "no digest found" in data["detail"].lower()


@pytest.mark.anyio
async def test_get_voice_missing_api_key(async_client: AsyncClient, monkeypatch):
    """Test GET /api/digest/{user_id}/voice returns 502 when GROQ_API_KEY is missing."""
    # First generate a digest for user_1
    gen_res = await async_client.post("/api/digest/user_1")
    assert gen_res.status_code == 200

    # Ensure GROQ_API_KEY is unset
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    res = await async_client.get("/api/digest/user_1/voice")
    assert res.status_code == 502
    data = res.json()
    assert "groq_api_key" in data["detail"].lower()


@pytest.mark.anyio
async def test_get_voice_success_mocked(async_client: AsyncClient, monkeypatch):
    """Test GET /api/digest/{user_id}/voice returns 200 audio/wav content when TTS call succeeds."""
    # 1. Generate digest for user_1
    gen_res = await async_client.post("/api/digest/user_1")
    assert gen_res.status_code == 200

    # 2. Patch generate_voice_digest in digest router
    fake_wav = _create_synthetic_wav(frames_count=100)

    def fake_generate(summary_prose: str, voice: str = "autumn"):
        return fake_wav

    monkeypatch.setattr("app.routers.digest.generate_voice_digest", fake_generate)

    res = await async_client.get("/api/digest/user_1/voice")
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    assert res.content == fake_wav
    assert "digest_voice_user_1.wav" in res.headers.get("content-disposition", "")
