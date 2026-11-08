import hmac
import time

import streamlit as st

from core.analytics import dashboard
from core.config import get_settings
from core.i18n import t


def render(language="en"):
    def tr(key):
        return t(key, language)
    st.title(tr("admin"))
    settings = get_settings()
    if not st.session_state.get("admin_until", 0) > time.time():
        with st.form("admin_login"):
            password = st.text_input(tr("admin.password"), type="password", max_chars=256)
            submitted = st.form_submit_button(tr("admin.login"))
        if submitted:
            last = st.session_state.get("admin_attempt", 0)
            st.session_state["admin_attempt"] = time.time()
            if (
                time.time() - last >= 2
                and settings.admin_password
                and hmac.compare_digest(password.encode(), settings.admin_password.encode())
            ):
                st.session_state["admin_until"] = time.time() + 1800
                st.rerun()
            st.error(tr("admin.failed"))
        return
    if st.button(tr("admin.logout")):
        st.session_state.pop("admin_until", None)
        st.rerun()
    if not settings.program_start_configured:
        st.error(tr("admin.start_warning"))
    if settings.database_url.startswith("sqlite"):
        st.warning(tr("admin.storage"))
    st.caption(tr("admin.missing"))
    data = dashboard()
    first = st.columns(3)
    first[0].metric(tr("admin.users"), data["users"])
    first[1].metric(tr("admin.dau"), data["dau"])
    first[2].metric(
        tr("admin.retention"),
        f"{data['retention']:.0%}" if data["retention"] is not None else tr("admin.na"),
    )
    st.caption(tr("admin.retention_note"))
    second = st.columns(3)
    second[0].metric(tr("admin.completion"), f"{data['completion']:.0%}")
    second[1].metric(
        tr("admin.call_score"),
        f"{data['call_score']:.1f}" if data["call_score"] is not None else tr("admin.na"),
    )
    second[2].metric(tr("admin.cost"), f"${data['cost']:.4f}")
    if data["user_rows"]:
        st.dataframe(data["user_rows"], hide_index=True, use_container_width=True)
    else:
        st.info(tr("admin.empty"))
