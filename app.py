"""Streamlit entry point. Run: streamlit run app.py."""

import time

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from core import auth, repo
from core.config import LANG_NAMES, LEVELS, SERVICE_LINES, UI_LANGS, get_settings
from core.content import validate_files
from core.i18n import t
from views import admin, calls, daily, practice, records, roadmap

st.set_page_config(page_title="Jamie · Workplace English", page_icon="💬", layout="wide")


@st.cache_resource
def verify_content():
    return validate_files()


def clear_learner_state():
    language = st.session_state.get("entry_language", "en")
    st.session_state.clear()
    st.session_state["entry_language"] = language


def sign_in(language):
    def tr(key):
        return t(key, language)
    st.title(tr("app"))
    st.subheader(tr("tagline"))
    st.caption(tr("privacy"))
    tabs = st.tabs([tr("login"), tr("signup")])
    with tabs[0]:
        with st.form("login"):
            email = st.text_input(tr("email"), max_chars=254)
            password = st.text_input(tr("password"), type="password", max_chars=256)
            submitted = st.form_submit_button(tr("login"), type="primary")
        if submitted:
            last = st.session_state.get("login_attempt", 0)
            st.session_state["login_attempt"] = time.time()
            token = auth.login(email, password) if time.time() - last >= 2 else None
            if token:
                clear_learner_state()
                st.query_params["s"] = token
                st.rerun()
            st.error(tr("login_failed"))
    with tabs[1]:
        with st.form("signup"):
            name = st.text_input(tr("name"), max_chars=80)
            email = st.text_input(tr("email"), key="signup_email", max_chars=254)
            password = st.text_input(
                tr("password"), type="password", key="signup_password", max_chars=256
            )
            code = st.text_input(tr("access"), type="password", max_chars=256)
            service = st.selectbox(tr("service"), SERVICE_LINES)
            level = st.selectbox(tr("level"), LEVELS)
            consent = st.checkbox(tr("consent"))
            submitted = st.form_submit_button(tr("signup"))
        if submitted:
            try:
                if not consent:
                    raise ValueError("consent")
                user = auth.create_user(email, password, name, service, level, language, code)
                token = auth.issue_session(user["id"])
            except (ValueError, SQLAlchemyError):
                st.error(tr("signup_failed"))
            else:
                clear_learner_state()
                st.query_params["s"] = token
                st.rerun()
    if get_settings().fake_ai:
        st.info(tr("demo"))
        if st.button(tr("demo_login")):
            from scripts.seed_demo import seed_demo

            token = auth.issue_session(seed_demo())
            clear_learner_state()
            st.query_params["s"] = token
            st.rerun()


def main():
    settings = get_settings()
    verify_content()
    token = st.query_params.get("s", "")
    user = auth.resolve_session(token)
    if not user:
        # Discard cached learner content if a token is expired or revoked in another tab.
        if st.session_state.get("learner_id"):
            clear_learner_state()
        language = st.sidebar.selectbox(
            "Language / 언어",
            UI_LANGS,
            index=1,
            format_func=lambda x: LANG_NAMES[x],
            key="entry_language",
        )
        admin_selected = st.sidebar.checkbox(t("admin", language), key="show_admin")
        if admin_selected:
            admin.render(language)
        else:
            sign_in(language)
        return
    if st.session_state.get("learner_id") != user["id"]:
        clear_learner_state()
        st.session_state["learner_id"] = user["id"]
    language = user["language"]

    def tr(key):
        return t(key, language)
    repo.visit(user["id"])
    st.sidebar.title("💬 Jamie")
    st.sidebar.caption(user["name"])
    pages = ["today", "calls", "review", "ask", "mistakes", "roadmap", "records", "admin"]
    page = st.sidebar.radio(tr("app"), pages, format_func=tr, key="navigation")
    st.sidebar.divider()
    if st.sidebar.button(tr("share")):
        st.sidebar.code(auth.share_url(settings.app_url), language=None)
    st.sidebar.caption(tr("share_caption"))
    if st.sidebar.button(tr("logout")):
        auth.logout(token)
        st.query_params.clear()
        clear_learner_state()
        st.rerun()
    if settings.fake_ai:
        st.info(tr("demo"))
    views = {
        "today": daily.render,
        "calls": calls.render,
        "review": practice.review,
        "ask": practice.ask,
        "mistakes": practice.mistakes,
        "roadmap": roadmap.render,
        "records": records.render,
        "admin": lambda u: admin.render(u["language"]),
    }
    views[page](user)


if __name__ == "__main__":
    try:
        main()
    except SQLAlchemyError:
        st.error(
            "Database unavailable. Check DATABASE_URL in Streamlit secrets. / 데이터베이스 연결을 확인하세요."
        )
