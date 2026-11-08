"""Check deploy prerequisites without revealing secrets or calling paid APIs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from core.auth import share_url  # noqa: E402
from core.config import get_settings  # noqa: E402
from core.content import validate_files  # noqa: E402
from core.db import get_engine  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", action="store_true", help="Require durable DB and live AI")
    args = parser.parse_args()
    errors = []
    settings = get_settings()
    if sys.version_info < (3, 11):
        errors.append("Python 3.11 or newer is required")
    try:
        lessons, scenarios = validate_files()
        print(f"Content: {lessons} lessons, {scenarios} scenarios")
    except (OSError, ValueError):
        errors.append("Content validation failed; run scripts/validate_content.py")
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database: connected")
    except Exception:
        errors.append("Database connection failed; check DATABASE_URL and installed driver")
    if args.production:
        if not settings.database_url.startswith("postgresql+psycopg://"):
            errors.append("Use PostgreSQL via postgresql+psycopg:// for durable hosted storage")
        if settings.fake_ai or not settings.openai_api_key:
            errors.append("Set FAKE_AI=0 and OPENAI_API_KEY for live AI")
        if not settings.program_start_configured:
            errors.append("Set a valid PROGRAM_START_DATE")
        for label, value in (
            ("PILOT_ACCESS_CODE", settings.pilot_access_code),
            ("ADMIN_PASSWORD", settings.admin_password),
        ):
            if not value or len(value) < 12 or value.startswith("change-me"):
                errors.append(f"Set a unique {label} with at least 12 characters")
        try:
            url = share_url(settings.app_url)
            if not url.startswith("https://") or "localhost" in url:
                raise ValueError()
        except ValueError:
            errors.append("Set APP_URL to the deployed HTTPS URL")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        raise SystemExit(1)
    print("Deployment preflight passed.")


if __name__ == "__main__":
    main()
