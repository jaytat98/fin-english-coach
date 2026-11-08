"""Application settings.

Reads Streamlit secrets first (when running inside Streamlit), then environment
variables / .env. Never hard-code secrets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from datetime import date
from functools import lru_cache

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ALLOWED_VOICES: tuple[str, ...] = ("alloy", "echo", "fable", "onyx", "nova", "shimmer")
COACH_NAME = "Jamie"
COACH_VOICE = "nova"
SERVICE_LINES: tuple[str, ...] = ("Audit", "Tax", "Deals", "Advisory")
LEVELS: tuple[str, ...] = ("Associate", "Senior", "Manager")
UI_LANGS: tuple[str, ...] = ("ko", "vi", "en")
LANG_NAMES: dict[str, str] = {"ko": "Korean", "vi": "Vietnamese", "en": "English"}


def _read(name: str, default: str | None = None) -> str | None:
    """Return a setting from Streamlit secrets (if available) or the environment."""
    try:
        import streamlit as st  # local import keeps core usable without Streamlit

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # no secrets file, not running in Streamlit, etc.
        pass
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _int(name: str, default: int) -> int:
    raw = _read(name)
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    raw = _read(name)
    try:
        return float(raw) if raw is not None else default
    except ValueError:
        return default


def _date(name: str, default: date) -> date:
    raw = _read(name)
    try:
        return date.fromisoformat(raw) if raw else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Prices:
    """USD prices used for cost ESTIMATES only.

    Verify against current OpenAI pricing before presenting numbers.
    """

    chat_input_per_1m: float = 0.15
    chat_output_per_1m: float = 0.60
    stt_per_minute: float = 0.003
    tts_per_1m_chars: float = 15.0
    tts_per_minute: float = 0.015
    tts_by_minute: bool = False


@dataclass(frozen=True)
class Limits:
    """Per-user daily limits and recording limits."""

    ai_calls_per_day: int = 120
    mock_calls_per_day: int = 5
    writing_attempts_per_lesson: int = 3
    ask_coach_per_day: int = 20
    custom_scenarios_per_day: int = 3
    reports_per_day: int = 1
    max_recording_seconds: int = 60
    min_recording_seconds: float = 0.8
    chat_history_messages: int = 20


@dataclass(frozen=True)
class Settings:
    """All runtime settings."""

    openai_api_key: str | None
    openai_model: str
    stt_model: str
    stt_fallback_model: str
    tts_model: str
    tts_fallback_model: str
    database_url: str
    pilot_access_code: str | None
    admin_password: str | None
    program_start_date: date
    app_timezone: str
    holiday_countries: tuple[str, ...]
    fake_ai: bool
    limits: Limits = field(default_factory=Limits)
    prices: Prices = field(default_factory=Prices)
    openai_model_strong: str = "gpt-4o"
    stt_model_shadowing: str = "gpt-4o-mini-transcribe"
    program_start_configured: bool = False
    strong_prices: Prices = field(default_factory=lambda: Prices(2.5, 10.0))
    app_url: str = "http://localhost:8501"

    @property
    def ai_enabled(self) -> bool:
        """True when AI features can run (real key or fake mode)."""
        return self.fake_ai or bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build settings once per process. Call get_settings.cache_clear() in tests."""
    limits = Limits(
        ai_calls_per_day=_int("LIMIT_AI_CALLS_PER_DAY", 120),
        mock_calls_per_day=_int("LIMIT_MOCK_CALLS_PER_DAY", 5),
        writing_attempts_per_lesson=_int("LIMIT_WRITING_ATTEMPTS", 3),
        ask_coach_per_day=_int("LIMIT_ASK_COACH_PER_DAY", 20),
        custom_scenarios_per_day=_int("LIMIT_CUSTOM_SCENARIOS_PER_DAY", 3),
        reports_per_day=_int("LIMIT_REPORTS_PER_DAY", 1),
        max_recording_seconds=_int("MAX_RECORDING_SECONDS", 60),
    )
    prices = Prices(
        chat_input_per_1m=_float("PRICE_CHAT_INPUT_PER_1M", 0.15),
        chat_output_per_1m=_float("PRICE_CHAT_OUTPUT_PER_1M", 0.60),
        stt_per_minute=_float("PRICE_STT_PER_MINUTE", 0.003),
        tts_per_1m_chars=_float("PRICE_TTS_PER_1M_CHARS", 15.0),
        tts_per_minute=_float("PRICE_TTS_PER_MINUTE", 0.015),
        tts_by_minute=(_read("OPENAI_TTS_MODEL", "gpt-4o-mini-tts") or "").startswith(
            "gpt-4o-mini-tts"
        ),
    )
    countries = tuple(
        c.strip().upper() for c in (_read("HOLIDAY_COUNTRIES", "VN") or "VN").split(",") if c
    )
    return Settings(
        openai_api_key=_read("OPENAI_API_KEY"),
        openai_model=_read("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
        stt_model=_read("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe") or "gpt-4o-mini-transcribe",
        stt_fallback_model="whisper-1",
        tts_model=_read("OPENAI_TTS_MODEL", "gpt-4o-mini-tts") or "gpt-4o-mini-tts",
        tts_fallback_model="tts-1",
        database_url=_read("DATABASE_URL", "sqlite:///data/app.db") or "sqlite:///data/app.db",
        pilot_access_code=_read("PILOT_ACCESS_CODE"),
        admin_password=_read("ADMIN_PASSWORD"),
        program_start_date=_date("PROGRAM_START_DATE", date.today()),
        app_timezone=_read("APP_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh",
        holiday_countries=countries or ("VN",),
        fake_ai=(_read("FAKE_AI", "0") or "0").strip() in ("1", "true", "True", "yes"),
        limits=limits,
        prices=prices,
        openai_model_strong=_read("OPENAI_MODEL_STRONG", "gpt-4o") or "gpt-4o",
        stt_model_shadowing=(
            _read("OPENAI_STT_MODEL_SHADOWING")
            or _read("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe")
            or "gpt-4o-mini-transcribe"
        ),
        program_start_configured=_valid_program_start(),
        strong_prices=replace(
            prices,
            chat_input_per_1m=_float("PRICE_STRONG_INPUT_PER_1M", 2.5),
            chat_output_per_1m=_float("PRICE_STRONG_OUTPUT_PER_1M", 10.0),
        ),
        app_url=_read("APP_URL", "http://localhost:8501") or "http://localhost:8501",
    )


def estimate_cost(
    prices: Prices,
    tokens_in: int = 0,
    tokens_out: int = 0,
    audio_sec: float = 0.0,
    tts_chars: int = 0,
) -> float:
    """Return an estimated USD cost for one API call (rounded to 6 decimals)."""
    cost = (
        tokens_in / 1_000_000 * prices.chat_input_per_1m
        + tokens_out / 1_000_000 * prices.chat_output_per_1m
        + audio_sec / 60 * prices.stt_per_minute
        + (tts_chars / 900 * prices.tts_per_minute if prices.tts_by_minute
           else tts_chars / 1_000_000 * prices.tts_per_1m_chars)
    )
    return round(cost, 6)


def _valid_program_start() -> bool:
    try:
        date.fromisoformat(_read("PROGRAM_START_DATE") or "")
        return True
    except ValueError:
        return False


STRONG_OPERATIONS = frozenset({"call_evaluator", "custom_scenario", "weekly_report", "cohort_report"})


def model_for(operation: str) -> tuple[str, Prices]:
    settings = get_settings()
    if operation in STRONG_OPERATIONS:
        return settings.openai_model_strong, settings.strong_prices
    return settings.openai_model, settings.prices
