"""Aggregate admin metrics. Demo call scores are excluded from real assessment."""

from datetime import date, timedelta

from sqlalchemy import select

from core import db, repo


def dashboard():
    with db.get_engine().connect() as connection:
        users = [dict(row) for row in connection.execute(select(db.users)).mappings()]
        visits = [dict(row) for row in connection.execute(select(db.visits)).mappings()]
        completions = list(connection.execute(select(db.completions)).mappings())
        calls = list(connection.execute(select(db.calls)).mappings())
        usage = list(connection.execute(select(db.usage)).mappings())
    today = repo.today()
    active = {(row["user_id"], row["day"]) for row in visits}
    eligible = [
        u for u in users if date.fromisoformat(u["created_at"][:10]) <= today - timedelta(days=7)
    ]
    retained = sum(
        (u["id"], (date.fromisoformat(u["created_at"][:10]) + timedelta(days=7)).isoformat())
        in active
        for u in eligible
    )
    real_scores = [row["score"] for row in calls if not row["fake"]]
    return {
        "users": len(users),
        "dau": sum(day == today.isoformat() for _, day in active),
        "retention": retained / len(eligible) if eligible else None,
        "completion": len(completions) / (30 * len(users)) if users else 0,
        "call_score": sum(real_scores) / len(real_scores) if real_scores else None,
        "cost": sum(row["cost"] for row in usage),
        "user_rows": [
            {key: row[key] for key in ("name", "email", "service_line", "created_at")}
            for row in users
        ],
    }
