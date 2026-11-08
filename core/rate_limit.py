"""Atomic per-user daily quotas, including simultaneous sessions."""

from sqlalchemy import update

from core import db
from core.repo import today


def reserve(user_id: str, kind: str, maximum: int) -> None:
    with db.get_engine().begin() as connection:
        values = dict(user_id=user_id, day=today().isoformat(), kind=kind, count=0)
        db.insert_once(connection, db.limits, values, ["user_id", "day", "kind"])
        result = connection.execute(
            update(db.limits)
            .where(
                db.limits.c.user_id == user_id,
                db.limits.c.day == values["day"],
                db.limits.c.kind == kind,
                db.limits.c.count < maximum,
            )
            .values(count=db.limits.c.count + 1)
        )
        if result.rowcount != 1:
            raise ValueError("daily_limit")
