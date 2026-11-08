import json
from datetime import date

import streamlit as st

from components.common import text
from core import db, repo
from core.calendar_service import holidays
from core.config import LEVELS, SERVICE_LINES, UI_LANGS
from core.workdays import current_streak


def render(user):
    st.title(text(user, "records"))
    completed = repo.rows(db.completions, user["id"])
    calls = repo.rows(db.calls, user["id"])
    dates = {date.fromisoformat(row["completed_date"]) for row in completed if row["on_time"]}
    columns = st.columns(3)
    columns[0].metric(text(user, "lessons_count"), len(completed))
    columns[1].metric(
        text(user, "streak"),
        current_streak(dates, repo.today(), date.fromisoformat(user["start_date"]), holidays()),
    )
    columns[2].metric(text(user, "calls_count"), len(calls))
    for call in sorted(calls, key=lambda c: c["created_at"], reverse=True)[:10]:
        with st.expander(f"{call['scenario_id']} · {call['score']} / 100"):
            result = json.loads(call["feedback"])
            if call["fake"]:
                st.caption(text(user, "demo"))
            st.write(result["summary"])
            st.write(result["next_step"])
    st.subheader(text(user, "settings"))
    with st.form("settings"):
        language = st.selectbox(
            text(user, "language"), UI_LANGS, index=UI_LANGS.index(user["language"])
        )
        service = st.selectbox(
            text(user, "service"), SERVICE_LINES, index=SERVICE_LINES.index(user["service_line"])
        )
        level = st.selectbox(text(user, "level"), LEVELS, index=LEVELS.index(user["level"]))
        if st.form_submit_button(text(user, "save_settings")):
            repo.update_profile(user["id"], language, service, level)
            st.rerun()
    export = {"profile": {k: v for k, v in user.items() if k != "password_hash"}}
    for table in (
        db.progress,
        db.completions,
        db.calls,
        db.reviews,
        db.mistakes,
        db.feedback,
        db.usage,
    ):
        export[table.name] = repo.rows(table, user["id"])
    st.download_button(
        text(user, "export"),
        json.dumps(export, ensure_ascii=False, indent=2),
        file_name="my-learning-data.json",
        mime="application/json",
    )
    with st.expander(text(user, "feedback_title")):
        with st.form("feedback"):
            rating = st.slider(text(user, "rating"), 1, 5, 4)
            message = st.text_area(text(user, "message"), max_chars=2000)
            if st.form_submit_button(text(user, "send")):
                repo.save_feedback(user["id"], rating, message)
                st.success(text(user, "saved"))
    with st.expander(text(user, "delete")):
        confirmed = st.checkbox(text(user, "delete_confirm"))
        if st.button(text(user, "delete"), disabled=not confirmed):
            repo.delete_user(user["id"])
            st.query_params.clear()
            st.session_state.clear()
            st.rerun()
