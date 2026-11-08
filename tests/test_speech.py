import io
import wave
from types import SimpleNamespace

from core import speech


def test_static_cache_precedes_dynamic_and_api(storage, tmp_path, monkeypatch):
    monkeypatch.setattr(speech, "CACHE", tmp_path)
    name = speech.cache_key("Hello", "gpt-4o-mini-tts", "nova")
    for directory, content in (("static", b"static"), ("dynamic", b"dynamic")):
        (tmp_path / directory).mkdir()
        (tmp_path / directory / name).write_bytes(content)
    assert speech.synthesize("Hello").read_bytes() == b"static"


def test_cache_key_separates_voices_and_models():
    assert speech.cache_key("Hello", "tts-1", "nova") != speech.cache_key("Hello", "tts-1", "onyx")
    assert speech.cache_key("Hello", "tts-1", "nova") != speech.cache_key("Hello", "other", "nova")


def test_shadowing_no_prompt_hint(learner, monkeypatch):
    from dataclasses import replace

    from core.config import get_settings

    received = {}

    def create(**kwargs):
        received.update(kwargs)
        return SimpleNamespace(text="Actual speech")

    monkeypatch.setattr(
        speech,
        "get_settings",
        lambda: replace(
            get_settings(), fake_ai=False, openai_api_key="test", stt_model_shadowing="shadow-model"
        ),
    )
    import openai

    monkeypatch.setattr(
        openai,
        "OpenAI",
        lambda **kwargs: SimpleNamespace(
            audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create))
        ),
    )
    audio = io.BytesIO()
    with wave.open(audio, "wb") as recording:
        recording.setnchannels(1)
        recording.setsampwidth(2)
        recording.setframerate(16000)
        recording.writeframes(b"\0\0" * 16000)
    assert speech.transcribe(audio.getvalue(), learner["id"], shadowing=True) == "Actual speech"
    assert received["model"] == "shadow-model"
    assert received["temperature"] == 0
    assert "prompt" not in received
