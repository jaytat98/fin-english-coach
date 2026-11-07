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