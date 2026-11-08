from datetime import date

from core.workdays import (
    current_streak,
    lesson_date_for,
    lesson_day_for,
    longest_streak,
    program_week,
)

START = date(2025, 3, 3)  # Monday
WEEK1 = {date(2025, 3, d) for d in range(3, 8)}  # Mon-Fri


def test_lesson_day_basic():
    assert lesson_day_for(date(2025, 3, 3), START, 30).day == 1
    assert lesson_day_for(date(2025, 3, 7), START, 30).day == 5
    assert lesson_day_for(date(2025, 3, 8), START, 30).day == 5  # Saturday
    assert lesson_day_for(date(2025, 3, 10), START, 30).day == 6


def test_before_start_is_preview():
    r = lesson_day_for(date(2025, 3, 1), START, 30)
    assert (r.day, r.state) == (1, "preview")


def test_holiday_skipped():
    holidays = frozenset({date(2025, 3, 5)})
    assert lesson_day_for(date(2025, 3, 7), START, 30, holidays).day == 4


def test_finished_program():
    r = lesson_day_for(date(2025, 3, 7), START, 3)
    assert (r.day, r.state) == (3, "finished")


def test_lesson_date_for():
    assert lesson_date_for(1, START) == START
    assert lesson_date_for(6, START) == date(2025, 3, 10)


def test_streak_not_broken_by_weekend():
    assert current_streak(WEEK1, date(2025, 3, 10), START) == 5  # Monday, not done yet
    assert current_streak(WEEK1, date(2025, 3, 8), START) == 5  # Saturday
    assert current_streak(WEEK1 | {date(2025, 3, 10)}, date(2025, 3, 10), START) == 6


def test_streak_broken_by_missed_working_day():
    done = {date(2025, 3, 6), date(2025, 3, 7)}
    assert current_streak(done, date(2025, 3, 7), START) == 2
    assert current_streak(done, date(2025, 3, 11), START) == 0  # missed Monday 10th


def test_longest_streak():
    done = WEEK1 | {date(2025, 3, 10), date(2025, 3, 12)}
    assert longest_streak(done) == 6


def test_program_week():
    assert [program_week(d) for d in (1, 5, 6, 30)] == [1, 1, 2, 6]