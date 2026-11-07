from core.scoring import LearnerStats, call_overall_score, earned_badges

ALL = ("task_completion", "clarity", "politeness_tone", "handling_pushback",
       "vocabulary", "grammar")


def scores(v):
    return {k: v for k in ALL}


def test_weighted_scores():
    assert call_overall_score(scores(10)) == 100
    assert call_overall_score(scores(5)) == 50


def test_hint_penalty_capped():
    assert call_overall_score(scores(10), hints_used=2) == 94
    assert call_overall_score(scores(10), hints_used=10) == 85


def test_phrase_bonus_capped_and_clamped():
    assert call_overall_score(scores(5), phrases_used=5) == 60
    assert call_overall_score(scores(5), phrases_used=50) == 60
    assert call_overall_score(scores(10), phrases_used=5) == 100


def test_voicemail_excludes_pushback():
    s = scores(10)
    s["handling_pushback"] = 1
    assert call_overall_score(s, is_voicemail=True) == 100
    assert call_overall_score(s, is_voicemail=False) < 100


def test_invalid_subscores_are_clamped():
    s = scores(15)
    s["grammar"] = "bad"
    assert 0 <= call_overall_score(s) <= 100


def test_badges():
    assert earned_badges(LearnerStats()) == set()
    got = earned_badges(LearnerStats(lessons_completed=1, current_streak=7, calls_completed=5))
    assert {"first_lesson", "streak_3", "streak_7", "first_call", "five_calls"} <= got
    assert "streak_15" not in got