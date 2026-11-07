"""Mock-call overall score and badge rules."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

SUBSCORE_KEYS: tuple[str, ...] = (
    "task_completion", "clarity", "politeness_tone",
    "handling_pushback", "vocabulary", "grammar",
)
WEIGHTS: dict[str, float] = {
    "task_completion": 0.30,
    "clarity": 0.15,
    "politeness_tone": 0.15,
    "handling_pushback": 0.15,
    "vocabulary": 0.15,
    "grammar": 0.10,
}
HINT_PENALTY = 3
HINT_PENALTY_CAP = 15
PHRASE_BONUS = 2
PHRASE_BONUS_CAP = 10


def _clamp_subscore(value: object) -> float:
    try:
        v = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        v = 1.0
    return min(10.0, max(1.0, v))


def call_overall_score(
    scores: dict[str, object],
    hints_used: int = 0,
    phrases_used: int = 0,
    is_voicemail: bool = False,
) -> int:
    """Weighted 0-100 score. Voicemail excludes handling_pushback (weights renormalized)."""
    weights = {
        k: w for k, w in WEIGHTS.items() if not (is_voicemail and k == "handling_pushback")
    }
    total_weight = sum(weights.values())
    mean = sum(w * _clamp_subscore(scores.get(k, 1)) for k, w in weights.items()) / total_weight
    penalty = min(HINT_PENALTY_CAP, HINT_PENALTY * max(0, hints_used))
    bonus = min(PHRASE_BONUS_CAP, PHRASE_BONUS * max(0, phrases_used))
    return int(max(0, min(100, round(mean * 10 - penalty + bonus))))


@dataclass(frozen=True)
class LearnerStats:
    """Aggregated numbers used to evaluate badges."""

    lessons_completed: int = 0
    current_streak: int = 0
    weekly_quiz_perfect: bool = False
    best_speaking: int = 0
    calls_completed: int = 0
    best_hard_call: int = 0
    best_call_improvement: int = 0  # same scenario: latest - first
    rehearsals_created: int = 0
    drill_days: int = 0
    patterns_mastered: int = 0


BADGE_RULES: dict[str, Callable[[LearnerStats], bool]] = {
    "first_lesson": lambda s: s.lessons_completed >= 1,
    "streak_3": lambda s: s.current_streak >= 3,
    "streak_7": lambda s: s.current_streak >= 7,
    "streak_15": lambda s: s.current_streak >= 15,
    "weekly_quiz_perfect": lambda s: s.weekly_quiz_perfect,
    "speaking_90": lambda s: s.best_speaking >= 90,
    "first_call": lambda s: s.calls_completed >= 1,
    "five_calls": lambda s: s.calls_completed >= 5,
    "hard_call_80": lambda s: s.best_hard_call >= 80,
    "call_improved_20": lambda s: s.best_call_improvement >= 20,
    "first_rehearsal": lambda s: s.rehearsals_created >= 1,
    "drills_7_days": lambda s: s.drill_days >= 7,
    "first_pattern_mastered": lambda s: s.patterns_mastered >= 1,
    "three_patterns_mastered": lambda s: s.patterns_mastered >= 3,
}


def earned_badges(stats: LearnerStats) -> set[str]:
    """Badge ids the learner qualifies for (caller stores only new ones)."""
    return {badge_id for badge_id, rule in BADGE_RULES.items() if rule(stats)}