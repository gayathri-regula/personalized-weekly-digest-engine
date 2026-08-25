"""Service for generating Text-to-Speech voice audio from digest summary prose using OpenAI API."""

import os
from typing import Any, Optional


def generate_voice_digest(
    summary_prose: str,
    voice: str = "alloy",
    client: Optional[Any] = None,
    timeout: float = 30.0,
) -> bytes:
    """Generate MP3 audio bytes for digest summary prose using OpenAI TTS model (tts-1).

    Args:
        summary_prose: Executive summary prose text to convert to speech.
        voice: OpenAI voice model identifier (default: "alloy").
        client: Optional injected OpenAI client or mock client for testing.
        timeout: API request timeout in seconds.

    Returns:
        bytes: Binary MP3 audio payload returned by OpenAI Speech API.

    Raises:
        ValueError: If summary prose is empty or OPENAI_API_KEY environment variable is missing.
        RuntimeError: If OpenAI TTS generation API call fails.
    """
    if not summary_prose or not summary_prose.strip():
        raise ValueError("Summary prose text cannot be empty.")

    # Truncate summary_prose as a simple safeguard if it exceeds 4000 characters
    clean_input = summary_prose.strip()
    if len(clean_input) > 4000:
        clean_input = clean_input[:4000]

    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is missing or empty."
            )
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=timeout)
        except ImportError as imp_err:
            raise ValueError(
                f"OPENAI_API_KEY is present but openai package is missing: {imp_err}"
            ) from imp_err

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=clean_input,
            response_format="mp3",
        )
        if hasattr(response, "content") and response.content is not None:
            return response.content
        elif hasattr(response, "read") and callable(response.read):
            return response.read()
        elif isinstance(response, bytes):
            return response
        else:
            raise RuntimeError("Unexpected audio response format from OpenAI Voice API.")
    except Exception as exc:
        raise RuntimeError(f"OpenAI Voice TTS generation failed: {exc}") from exc
