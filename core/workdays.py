"""Simplified SM-2 spaced repetition (deterministic, date-based)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

Rating = Literal["again", "hard", "good", "easy"]
RATINGS: tuple[Rating, ...] = ("again", "hard", "good", "easy")

EASE_START = 2.5
EASE_MIN = 1.3
EASE_MAX = 3.0
LEARNED_THRESHOLD_DAYS = 21


@dataclass(frozen=True)
class CardState:
    """Scheduling state of one review card."""

    ease: float = EASE_START
    interval_days: int = 0
    reps: int = 0
    due_date: date | None = None
    learned: bool = False


def _clamp_ease(value: float) -> float:
    return round(min(EASE_MAX, max(EASE_MIN, value)), 2)


def next_values(state: CardState, rating: Rating) -> tuple[int, int, float]:
    """Return (interval_days, reps, ease) after a rating, without dates."""
    interval, reps, ease = state.interval_days, state.reps, state.ease
    if rating == "again":
        return 0, 0, _clamp_ease(ease - 0.20)
    if rating == "hard":
        return max(1, round(interval * 1.2)), reps, _clamp_ease(ease - 0.15)
    if rating == "good":
        if reps == 0:
            new_interval = 1
        elif reps == 1:
            new_interval = 3
        else:
            new_interval = max(interval + 1, round(interval * ease))
        return new_interval, reps + 1, ease
    if rating == "easy":
        if reps == 0:
            new_interval = 3
        else:
            new_interval = max(interval + 1, round(interval * ease * 1.3))
        return new_interval, reps + 1, _clamp_ease(ease + 0.15)
    raise ValueError(f"Unknown rating: {rating}")


def review(state: CardState, rating: Rating, today: date) -> CardState:
    """Apply a rating and return the new card state.

    'again' sets interval 0 and due today; the review session should show the
    card again at the end of the current session.
    """
    interval, reps, ease = next_values(state, rating)
    return CardState(
        ease=ease,
        interval_days=interval,
        reps=reps,
        due_date=today + timedelta(days=interval),
        learned=interval >= LEARNED_THRESHOLD_DAYS,
    )


def preview(state: CardState) -> dict[str, int]:
    """Interval (days) each rating would produce - shown under the rating buttons."""
    return {r: next_values(state, r)[0] for r in RATINGS}


def is_due(state: CardState, today: date) -> bool:
    """New cards (no due date) are due immediately."""
    return state.due_date is None or state.due_date <= today


# The supplied file duplicated srs.py. Preserve its public API and add the
# missing calendar API required by HANDOFF.md and the supplied workday tests.
@dataclass(frozen=True)
class LessonDay:
    day: int
    state: Literal["preview", "active", "finished"]


def load_holidays(path, countries=("VN",)) -> frozenset[date]:
    """Read [{date: ISO date, country: code, ...}] without inventing missing data.

    The supplied holiday file is absent; fail explicitly until it is restored.
    """
    import json
    from pathlib import Path

    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    selected = {country.upper() for country in countries}
    return frozenset(
        date.fromisoformat(row["date"])
        for row in rows if row["country"].upper() in selected
    )


def is_working_day(day: date, holidays=frozenset()) -> bool:
    return day.weekday() < 5 and day not in holidays


def lesson_day_for(today: date, start: date, total: int = 30,
                   holidays=frozenset()) -> LessonDay:
    if total < 1:
        raise ValueError("total must be positive")
    if today < start:
        return LessonDay(1, "preview")
    day, count = start, 0
    while day <= today:
        count += is_working_day(day, holidays)
        if count > total:
            return LessonDay(total, "finished")
        day += timedelta(days=1)
    return LessonDay(max(1, count), "active" if count else "preview")


def lesson_date_for(day: int, start: date, holidays=frozenset()) -> date:
    if day < 1:
        raise ValueError("day must be positive")
    cursor, count = start, 0
    while True:
        count += is_working_day(cursor, holidays)
        if count == day:
            return cursor
        cursor += timedelta(days=1)


def current_streak(done: set[date], today: date, start: date,
                   holidays=frozenset()) -> int:
    """Count on-time completions; today's unfinished lesson has a grace period."""
    cursor, count = today, 0
    if cursor not in done or not is_working_day(cursor, holidays):
        cursor -= timedelta(days=1)
    while cursor >= start:
        if is_working_day(cursor, holidays):
            if cursor not in done:
                break
            count += 1
        cursor -= timedelta(days=1)
    return count


def longest_streak(done: set[date], holidays=frozenset()) -> int:
    previous, count, best = None, 0, 0
    for day in sorted(d for d in done if is_working_day(d, holidays)):
        expected = lesson_date_for(1, previous + timedelta(days=1), holidays) if previous else None
        count = count + 1 if day == expected else 1
        best = max(best, count)
        previous = day
    return best


def program_week(day: int) -> int:
    if day < 1:
        raise ValueError("day must be positive")
    return (day - 1) // 5 + 1
