"""Audio cache and transcription. Shadowing never receives the target as a hint."""

import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import wave
from dataclasses import replace
from pathlib import Path

from core.config import ALLOWED_VOICES, estimate_cost, get_settings
from core.llm import AIUnavailable, log_usage
from core.rate_limit import reserve

CACHE = Path(__file__).resolve().parents[1] / "audio_cache"


def cache_key(text: str, model: str, voice: str) -> str:
    data = json.dumps([text, model, voice, "mp3"], ensure_ascii=False)
    return hashlib.sha256(data.encode()).hexdigest() + ".mp3"


def dynamic_folder(user_id=None):
    if user_id is not None and not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", user_id):
        raise ValueError("Invalid audio owner")
    return CACHE / "dynamic" / user_id if user_id else CACHE / "dynamic"


def clear_user_audio(user_id):
    folder = dynamic_folder(user_id)
    if folder.exists():
        shutil.rmtree(folder)


def synthesize(text: str, voice="nova", user_id=None, *, static=False) -> Path | None:
    settings = get_settings()
    if voice not in ALLOWED_VOICES or not text.strip() or len(text) > 4096:
        raise ValueError("Invalid speech input")
    name = cache_key(text, settings.tts_model, voice)
    for folder in (CACHE / "static", dynamic_folder(user_id)):
        path = folder / name
        if path.is_file() and path.stat().st_size:
            if static and folder != CACHE / "static":
                break
            return path
    if settings.fake_ai:
        return None
    if not settings.openai_api_key:
        raise AIUnavailable("ai_unavailable")
    if user_id:
        reserve(user_id, "ai", settings.limits.ai_calls_per_day)
    from openai import OpenAI

    try:
        result = OpenAI(
            api_key=settings.openai_api_key, timeout=45, max_retries=1
        ).audio.speech.create(
            model=settings.tts_model,
            voice=voice,
            input=text,
            response_format="mp3",
        )
        folder = CACHE / "static" if static else dynamic_folder(user_id)
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=folder, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(result.content)
        try:
            os.replace(temporary, folder / name)
        finally:
            temporary.unlink(missing_ok=True)
        if user_id:
            log_usage(
                user_id,
                "tts",
                settings.tts_model,
                estimate_cost(settings.prices, tts_chars=len(text)),
                False,
            )
        return folder / name
    except Exception as error:
        raise AIUnavailable("ai_failed") from error


def transcribe(audio: bytes, user_id: str, *, shadowing=False) -> str:
    settings = get_settings()
    if len(audio) > 10 * 1024 * 1024:
        raise ValueError("recording_length")
    try:
        with wave.open(io.BytesIO(audio)) as recording:
            seconds = recording.getnframes() / recording.getframerate()
    except (wave.Error, EOFError) as error:
        raise ValueError("invalid_audio") from error
    if (
        not settings.limits.min_recording_seconds
        <= seconds
        <= settings.limits.max_recording_seconds
    ):
        raise ValueError("recording_length")
    if settings.fake_ai or not settings.openai_api_key:
        raise AIUnavailable("transcription_unavailable")
    reserve(user_id, "ai", settings.limits.ai_calls_per_day)
    model = settings.stt_model_shadowing if shadowing else settings.stt_model
    from openai import OpenAI

    try:
        response = OpenAI(api_key=settings.openai_api_key, timeout=45, max_retries=1)
        result = response.audio.transcriptions.create(
            model=model,
            file=("recording.wav", audio, "audio/wav"),
            temperature=0,
            response_format="json",
            language="en",
        )
        # STT pricing can differ for the separately configured shadowing model.
        prices = replace(settings.prices, stt_per_minute=settings.prices.stt_per_minute)
        log_usage(
            user_id,
            "shadowing_stt" if shadowing else "stt",
            model,
            estimate_cost(prices, audio_sec=seconds),
            False,
        )
        return result.text
    except Exception as error:
        raise AIUnavailable("ai_failed") from error
