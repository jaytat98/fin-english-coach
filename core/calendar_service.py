"""Explicit missing-holiday fallback for the app; never invent holiday dates."""

from pathlib import Path

from core.config import get_settings
from core.workdays import load_holidays

HOLIDAY_FILE = Path(__file__).resolve().parents[1] / "data/holidays.json"


def holidays():
    if not HOLIDAY_FILE.exists():
        return frozenset()
    return load_holidays(HOLIDAY_FILE, get_settings().holiday_countries)
