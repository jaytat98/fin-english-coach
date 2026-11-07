from datetime import date, timedelta

from core.srs import EASE_MIN, CardState, is_due, preview, review

TODAY = date(2025, 3, 3)


def test_good_sequence():
    s = review(CardState(), "good", TODAY)
    assert (s.interval_days, s.reps, s.due_date) == (1, 1, TODAY + timedelta(days=1))
    s = review(s, "good", TODAY)
    assert s.interval_days == 3
    s = review(s, "good", TODAY)
    assert s.interval_days == 8  # round(3 * 2.5)


def test_again_resets_and_lowers_ease():
    s = review(review(CardState(), "good", TODAY), "again", TODAY)
    assert s.interval_days == 0 and s.reps == 0
    assert s.due_date == TODAY
    assert s.ease == 2.3


def test_easy_first_time():
    s = review(CardState(), "easy", TODAY)
    assert s.interval_days == 3 and s.ease == 2.65


def test_hard_minimum_one_day():
    s = review(CardState(), "hard", TODAY)
    assert s.interval_days == 1 and s.ease == 2.35


def test_ease_clamped_to_min():
    s = CardState()
    for _ in range(20):
        s = review(s, "again", TODAY)
    assert s.ease == EASE_MIN


def test_learned_threshold():
    s = CardState(ease=2.5, interval_days=10, reps=3)
    s = review(s, "good", TODAY)
    assert s.interval_days == 25 and s.learned


def test_good_never_stalls():
    s = CardState(ease=1.3, interval_days=1, reps=2)
    assert review(s, "good", TODAY).interval_days >= 2


def test_preview_and_due():
    p = preview(CardState())
    assert p == {"again": 0, "hard": 1, "good": 1, "easy": 3}
    assert is_due(CardState(), TODAY)
    assert not is_due(CardState(due_date=TODAY + timedelta(days=1)), TODAY)