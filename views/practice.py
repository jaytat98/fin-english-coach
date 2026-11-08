import streamlit as st

from components.common import attempt, show_feedback, text
from core import db, repo
from core.llm import generate
from core.patterns import PATTERNS
from core.srs import is_due


def review(user):
    st.title(text(user, "review"))
    cards = repo.rows(db.reviews, user["id"])
    due = [card for card in cards if is_due(repo.card_state(card), repo.today())]
    if not due:
        st.success(text(user, "no_due" if cards else "no_cards"))
        return
    card = due[st.session_state.get("review_index", 0) % len(due)]
    st.caption(f"{len(due)}")
    st.header(card["front"])
    reveal_key = f"reveal:{card['card_id']}"
    if st.button(text(user, "reveal")):
        st.session_state[reveal_key] = True
    if st.session_state.get(reveal_key):
        st.write(card["back"])
        for column, rating in zip(st.columns(4), ("again", "hard", "good", "easy")):
            if column.button(text(user, rating), use_container_width=True):
                repo.review_card(user["id"], card["card_id"], rating)
                st.session_state[reveal_key] = False
                st.session_state["review_index"] = st.session_state.get("review_index", 0) + 1
                st.rerun()


def ask(user):
    st.title(text(user, "ask"))
    st.caption(text(user, "privacy"))
    with st.form("ask_coach"):
        question = st.text_area(text(user, "question"), max_chars=2000)
        submitted = st.form_submit_button(text(user, "send"))
    if submitted and question.strip():
        result = attempt(user, lambda: generate("ask_coach", {"text": question}, user))
        if result:
            st.session_state["coach_answer"] = result
            repo.save_mistakes(user["id"], result.corrections)
    if "coach_answer" in st.session_state:
        show_feedback(st.session_state["coach_answer"])


def mistakes(user):
    st.title(text(user, "mistakes"))
    mistakes = [row for row in repo.rows(db.mistakes, user["id"]) if not row["resolved"]]
    if not mistakes:
        st.info(text(user, "no_mistakes"))
    for mistake in mistakes:
        pattern = PATTERNS.get(mistake["pattern_key"])
        with st.container(border=True):
            if pattern:
                st.subheader(pattern.label_ko if user["language"] == "ko" else pattern.label_en)
            st.error(mistake["wrong"])
            st.success(mistake["right"])
            st.write(mistake["note"])
            if st.button(text(user, "mastered"), key=mistake["id"]):
                repo.resolve_mistake(user["id"], mistake["id"])
                st.rerun()
