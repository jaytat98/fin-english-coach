from datetime import date

import streamlit as st

from components.common import text
from core import db, repo
from core.calendar_service import HOLIDAY_FILE, holidays
from core.content import load_lessons
from core.workdays import lesson_date_for


def render(user):
    st.title(text(user, "roadmap"))
    st.caption(text(user, "roadmap.intro"))
    if not HOLIDAY_FILE.exists():
        st.info(text(user, "roadmap.holidays"))
    completed = {row["day"] for row in repo.rows(db.completions, user["id"])}
    lessons = load_lessons()
    for week in range(1, 7):
        with st.expander(text(user, "roadmap.week", week=week), expanded=week == 1):
            for lesson in lessons[(week - 1) * 5 : week * 5]:
                scheduled = lesson_date_for(
                    lesson.day, date.fromisoformat(user["start_date"]), holidays()
                )
                title = lesson.theme_ko if user["language"] == "ko" else lesson.theme_en
                status = "roadmap.complete" if lesson.day in completed else "roadmap.upcoming"
                st.write(f"{'✓' if lesson.day in completed else '○'} {lesson.day}. {title}")
                st.caption(f"{scheduled.isoformat()} · {text(user, status)}")
