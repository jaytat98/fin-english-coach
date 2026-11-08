"""Create the shared, explicitly fake demo account idempotently."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from core import db, repo  # noqa: E402
from core.auth import hash_password, now  # noqa: E402
from core.config import get_settings  # noqa: E402

DEMO_ID = "demo-learner"


def seed_demo():
    settings = get_settings()
    if not settings.fake_ai:
        raise ValueError("Enable FAKE_AI=1 before creating demo data")
    with db.get_engine().begin() as connection:
        existing = connection.execute(select(db.users).where(db.users.c.id == DEMO_ID)).first()
        if not existing:
            db.insert_once(
                connection,
                db.users,
                dict(
                    id=DEMO_ID,
                    email="demo@example.test",
                    name="Demo learner",
                    password_hash=hash_password("Demo-practice-only-2026"),
                    service_line="Audit",
                    level="Senior",
                    language="en",
                    created_at=now(),
                    start_date=(
                        settings.program_start_date
                        if settings.program_start_configured
                        else repo.today() - timedelta(days=repo.today().weekday())
                    ).isoformat(),
                ),
                ["id"],
            )
    return DEMO_ID


if __name__ == "__main__":
    seed_demo()
    print("Demo account ready: use Explore the demo on the sign-in screen.")
