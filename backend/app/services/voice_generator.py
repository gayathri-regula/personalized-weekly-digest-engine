"""Service for generating Text-to-Speech voice audio from digest summary prose using Groq API."""

import io
import os
import re
import wave
from typing import Any, List, Optional


def chunk_text(text: str, max_chars: int = 200) -> List[str]:
    """Split text into segments of at most max_chars length, preferring sentence boundaries and spaces."""
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    if len(cleaned_text) <= max_chars:
        return [cleaned_text]

    raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
    sentences: List[str] = []

    for s in raw_sentences:
        s_str = s.strip()
        if not s_str:
            continue
        if len(s_str) <= max_chars:
            sentences.append(s_str)
        else:
            words = s_str.split()
            current_word_chunk: List[str] = []
            current_word_len = 0
            for word in words:
                added_len = len(word) if not current_word_chunk else len(word) + 1
                if current_word_len + added_len <= max_chars:
                    current_word_chunk.append(word)
                    current_word_len += added_len
                else:
                    if current_word_chunk:
                        sentences.append(" ".join(current_word_chunk))
                    current_word_chunk = [word]
                    current_word_len = len(word)
            if current_word_chunk:
                sentences.append(" ".join(current_word_chunk))

    chunks: List[str] = []
    current_chunk = ""

    for sentence in sentences:
        if not current_chunk:
            current_chunk = sentence
        elif len(current_chunk) + 1 + len(sentence) <= max_chars:
            current_chunk = f"{current_chunk} {sentence}"
        else:
            chunks.append(current_chunk)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def stitch_wav_chunks(wav_chunks: List[bytes]) -> bytes:
    """Stitch multiple WAV audio byte chunks into a single valid WAV byte stream."""
    if not wav_chunks:
        return b""
    if len(wav_chunks) == 1:
        return wav_chunks[0]

    params = None
    all_pcm_frames: List[bytes] = []

    for idx, chunk in enumerate(wav_chunks):
        if not chunk:
            continue
        with io.BytesIO(chunk) as in_buf:
            with wave.open(in_buf, "rb") as wav_in:
                chunk_params = wav_in.getparams()
                if params is None:
                    params = chunk_params
                else:
                    if (
                        chunk_params.nchannels != params.nchannels
                        or chunk_params.sampwidth != params.sampwidth
                        or chunk_params.framerate != params.framerate
                        or chunk_params.comptype != params.comptype
                    ):
                        raise RuntimeError(
                            f"Incompatible WAV audio parameters in chunk {idx}: "
                            f"{chunk_params} vs expected {params}"
                        )
                all_pcm_frames.append(wav_in.readframes(wav_in.getnframes()))

    if params is None:
        return b""

    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wav_out:
        wav_out.setnchannels(params.nchannels)
        wav_out.setsampwidth(params.sampwidth)
        wav_out.setframerate(params.framerate)
        wav_out.setcomptype(params.comptype, params.compname)
        for pcm_frames in all_pcm_frames:
            wav_out.writeframes(pcm_frames)

    return out_buf.getvalue()


def generate_voice_digest(
    summary_prose: str,
    voice: str = "autumn",
    client: Optional[Any] = None,
    timeout: float = 30.0,
) -> bytes:
    """Generate WAV audio bytes for digest summary prose using Groq Orpheus TTS model with text chunking.

    Args:
        summary_prose: Executive summary prose text to convert to speech.
        voice: Groq Orpheus voice model identifier (default: "autumn").
        client: Optional injected Groq client or mock client for testing.
        timeout: API request timeout in seconds.

    Returns:
        bytes: Binary WAV audio payload stitched from all audio chunks.

    Raises:
        ValueError: If summary prose is empty or GROQ_API_KEY environment variable is missing.
        RuntimeError: If Groq TTS generation API call fails.
    """
    if not summary_prose or not summary_prose.strip():
        raise ValueError("Summary prose text cannot be empty.")

    if client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is missing or empty."
            )
        try:
            import groq

            client = groq.Groq(api_key=api_key, timeout=timeout)
        except ImportError as imp_err:
            raise ValueError(
                f"GROQ_API_KEY is present but groq package is missing: {imp_err}"
            ) from imp_err

    text_chunks = chunk_text(summary_prose, max_chars=200)
    audio_chunks: List[bytes] = []

    try:
        for chunk in text_chunks:
            response = client.audio.speech.create(
                model="canopylabs/orpheus-v1-english",
                voice=voice,
                input=chunk,
                response_format="wav",
            )
            if hasattr(response, "content") and response.content is not None:
                audio_chunks.append(response.content)
            elif hasattr(response, "read") and callable(response.read):
                audio_chunks.append(response.read())
            elif isinstance(response, bytes):
                audio_chunks.append(response)
            else:
                raise RuntimeError("Unexpected audio response format from Groq Voice API.")

        return stitch_wav_chunks(audio_chunks)
    except Exception as exc:
        raise RuntimeError(f"Groq Voice TTS generation failed: {exc}") from exc

