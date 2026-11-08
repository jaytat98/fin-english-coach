"""User-scoped data access. No learner operation accepts another user's rows."""

import json
from dataclasses import asdict
from datetime import date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select, update

from core import db
from core.auth import now
from core.config import get_settings
from core.srs import CardState, review


def today() -> date:
    return datetime.now(ZoneInfo(get_settings().app_timezone)).date()


def rows(table, user_id: str) -> list[dict]:
    with db.get_engine().connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                select(table).where(table.c.user_id == user_id)
            ).mappings()
        ]


def visit(user_id):
    with db.get_engine().begin() as connection:
        db.insert_once(
            connection,
            db.visits,
            {"user_id": user_id, "day": today().isoformat()},
            ["user_id", "day"],
        )


def save_step(user_id, day, step, payload):
    with db.get_engine().begin() as connection:
        db.insert_once(
            connection,
            db.progress,
            dict(
                user_id=user_id,
                day=day,
                step=step,
                payload=json.dumps(payload, ensure_ascii=False),
                created_at=now(),
            ),
            ["user_id", "day", "step"],
        )


def completed_steps(user_id, day):
    return {r["step"] for r in rows(db.progress, user_id) if r["day"] == day}


def complete_lesson(user_id, day, scheduled_date):
    required = {"phrase", "terms", "tip", "speaking", "writing", "quiz", "reflection"}
    if not required.issubset(completed_steps(user_id, day)):
        raise ValueError("Complete every step first")
    with db.get_engine().begin() as connection:
        db.insert_once(
            connection,
            db.completions,
            dict(
                user_id=user_id,
                day=day,
                completed_date=today().isoformat(),
                on_time=int(today() == scheduled_date),
            ),
            ["user_id", "day"],
        )


def add_card(user_id, card_id, front, back):
    with db.get_engine().begin() as connection:
        db.insert_once(
            connection,
            db.reviews,
            dict(
                user_id=user_id,
                card_id=card_id,
                front=front,
                back=back,
                state=json.dumps(asdict(CardState())),
            ),
            ["user_id", "card_id"],
        )


def card_state(row):
    state = json.loads(row["state"])
    if state["due_date"]:
        state["due_date"] = date.fromisoformat(state["due_date"])
    return CardState(**state)


def review_card(user_id, card_id, rating):
    with db.get_engine().begin() as connection:
        row = (
            connection.execute(
                select(db.reviews)
                .where(db.reviews.c.user_id == user_id, db.reviews.c.card_id == card_id)
                .with_for_update()
            )
            .mappings()
            .one()
        )
        state = asdict(review(card_state(row), rating, today()))
        state["due_date"] = state["due_date"].isoformat()
        connection.execute(
            update(db.reviews)
            .where(db.reviews.c.user_id == user_id, db.reviews.c.card_id == card_id)
            .values(state=json.dumps(state))
        )


def save_call(user_id, call_id, scenario_id, score, transcript, evaluation, fake):
    with db.get_engine().begin() as connection:
        db.insert_once(
            connection,
            db.calls,
            dict(
                id=call_id,
                user_id=user_id,
                scenario_id=scenario_id,
                score=score,
                transcript=json.dumps(transcript, ensure_ascii=False),
                feedback=evaluation.model_dump_json(),
                created_at=now(),
                fake=int(fake),
            ),
            ["id"],
        )


def save_mistakes(user_id, corrections):
    from core.patterns import is_valid_key

    with db.get_engine().begin() as connection:
        for correction in corrections:
            if not is_valid_key(correction.pattern_key):
                continue
            connection.execute(
                db.mistakes.insert().values(
                    id=uuid4().hex,
                    user_id=user_id,
                    pattern_key=correction.pattern_key,
                    wrong=correction.wrong,
                    right=correction.right,
                    note=correction.explanation,
                    resolved=0,
                    created_at=now(),
                )
            )


def resolve_mistake(user_id, mistake_id):
    with db.get_engine().begin() as connection:
        connection.execute(
            update(db.mistakes)
            .where(db.mistakes.c.user_id == user_id, db.mistakes.c.id == mistake_id)
            .values(resolved=1)
        )


def update_profile(user_id, language, service_line, level):
    from core.config import LEVELS, SERVICE_LINES, UI_LANGS

    if language not in UI_LANGS or service_line not in SERVICE_LINES or level not in LEVELS:
        raise ValueError("invalid_profile")
    with db.get_engine().begin() as connection:
        connection.execute(
            update(db.users)
            .where(db.users.c.id == user_id)
            .values(
                language=language,
                service_line=service_line,
                level=level,
            )
        )


def delete_user(user_id):
    from core.speech import clear_user_audio

    with db.get_engine().begin() as connection:
        clear_user_audio(user_id)
        connection.execute(delete(db.users).where(db.users.c.id == user_id))


def save_feedback(user_id, rating, message):
    if rating not in range(1, 6) or len(message) > 2000:
        raise ValueError("Invalid feedback")
    with db.get_engine().begin() as connection:
        connection.execute(
            db.feedback.insert().values(
                id=uuid4().hex,
                user_id=user_id,
                rating=rating,
                message=message,
                created_at=now(),
            )
        )
