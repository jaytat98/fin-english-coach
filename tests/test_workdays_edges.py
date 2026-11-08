from datetime import date

import pytest

from core.workdays import (
    current_streak,
    is_working_day,
    lesson_date_for,
    lesson_day_for,
    longest_streak,
)


def test_holiday_does_not_break_streak():
    done = {date(2025, 3, 4), date(2025, 3, 6)}
    holidays = frozenset({date(2025, 3, 5)})
    assert longest_streak(done, holidays) == 2
    assert current_streak(done, date(2025, 3, 6), date(2025, 3, 3), holidays) == 2
    assert not is_working_day(date(2025, 3, 5), holidays)


def test_weekend_completions_do_not_count():
    done = {date(2025, 3, 7), date(2025, 3, 8)}
    assert longest_streak(done) == 1
    assert current_streak(done, date(2025, 3, 8), date(2025, 3, 3)) == 1


def test_last_lesson_remains_active_until_next_workday():
    start = date(2025, 3, 3)
    assert lesson_day_for(date(2025, 3, 8), start, 5).state == "active"
    assert lesson_day_for(date(2025, 3, 10), start, 5).state == "finished"


def test_nonworking_start():
    start = date(2025, 3, 8)
    assert lesson_day_for(start, start).state == "preview"
    assert lesson_date_for(1, start) == date(2025, 3, 10)


def test_invalid_day():
    with pytest.raises(ValueError):
        lesson_date_for(0, date(2025, 3, 3))
