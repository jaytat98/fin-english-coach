from datetime import date

import streamlit as st

from components.common import attempt, audio_transcript, listen, show_feedback, text
from core import db, repo
from core.calendar_service import HOLIDAY_FILE, holidays
from core.content import load_lessons
from core.llm import generate
from core.pronunciation import evaluate
from core.workdays import lesson_date_for, lesson_day_for


def render(user):
    lessons = load_lessons()
    start = date.fromisoformat(user["start_date"])
    current = lesson_day_for(repo.today(), start, 30, holidays())
    st.title(text(user, "today"))
    if current.state != "active":
        st.info(text(user, "finished" if current.state == "finished" else "preview"))
    if not HOLIDAY_FILE.exists():
        st.caption(text(user, "holidays_missing"))
    day = st.selectbox(text(user, "lesson_picker"), range(1, 31), index=current.day - 1)
    lesson = lessons[day - 1]
    theme = lesson.theme_ko if user["language"] == "ko" else lesson.theme_en
    st.subheader(text(user, "day", day=day, theme=theme))
    scheduled = lesson_date_for(day, start, holidays())
    future = scheduled > repo.today()
    if future:
        st.info(text(user, "preview"))
    steps = repo.completed_steps(user["id"], day)
    st.progress(len(steps) / 7, text=f"{len(steps)} / 7")
    with st.container(border=True):
        st.markdown(f"**{text(user, 'jamie_card')}**")
        st.write(text(user, "jamie_note"))
        st.write(lesson.phrase.examples[0].en)
    tabs = st.tabs(
        [
            text(user, key)
            for key in ("phrase", "terms", "tip", "speaking", "writing", "quiz", "reflection")
        ]
    )

    def mark(step, payload=None):
        if future:
            return
        repo.save_step(user["id"], day, step, payload or {})
        if step == "phrase":
            repo.add_card(
                user["id"], f"phrase:{day}", lesson.phrase.text, lesson.phrase.examples[0].en
            )
        if step == "terms":
            terms = (lesson.terms.common, *getattr(lesson.terms, user["service_line"]))
            for term in terms:
                repo.add_card(user["id"], f"term:{term.term}", term.term, term.definition_en)
        st.rerun()

    def mark_button(step):
        if step in steps:
            st.success(text(user, "done"))
        elif st.button(text(user, "mark"), key=f"mark:{day}:{step}", disabled=future):
            mark(step)

    with tabs[0]:
        st.header(lesson.phrase.text)
        if user["language"] == "ko":
            st.write(lesson.phrase.meaning_ko)
            st.info(lesson.phrase.nuance_ko)
        for example in lesson.phrase.examples:
            st.write(example.en)
            if user["language"] == "ko":
                st.caption(example.ko)
        listen(user, lesson.phrase.examples[0].en, f"phrase:{day}")
        mark_button("phrase")
    with tabs[1]:
        for term in (lesson.terms.common, *getattr(lesson.terms, user["service_line"])):
            with st.container(border=True):
                st.subheader(term.term)
                st.write(term.meaning_ko if user["language"] == "ko" else term.definition_en)
                st.write(term.example_en)
                if user["language"] == "ko":
                    st.caption(term.example_ko)
                listen(user, term.term, f"term:{day}:{term.term}")
        mark_button("terms")
    with tabs[2]:
        tip = lesson.konglish_tip
        if user["language"] == "ko":
            st.subheader(tip.title_ko)
        st.error(tip.wrong)
        st.success(tip.right)
        if user["language"] == "ko":
            st.write(tip.explanation_ko)
        mark_button("tip")
    with tabs[3]:
        st.write(lesson.speaking_sentence.en)
        if user["language"] == "ko":
            st.caption(lesson.speaking_sentence.ko)
        listen(user, lesson.speaking_sentence.en, f"speaking:{day}")
        transcript = audio_transcript(user, f"speaking:{day}", shadowing=True)
        st.caption(text(user, "approx"))
        if st.button(text(user, "compare"), disabled=not transcript.strip() or future):
            tokens, score = evaluate(lesson.speaking_sentence.en, transcript)
            st.session_state[f"speaking_result:{day}"] = (tokens, score)
            repo.save_step(user["id"], day, "speaking", {"score": score, "transcript": transcript})
        result = st.session_state.get(f"speaking_result:{day}")
        if result:
            st.metric(text(user, "match"), f"{result[1]} / 100")
            st.write(
                " · ".join(
                    f"{'✓' if token.status == 'correct' else '△'} {token.word}"
                    for token in result[0]
                )
            )
    with tabs[4]:
        st.write(
            lesson.writing_task.instruction_ko
            if user["language"] == "ko"
            else text(user, "write_instruction")
        )
        st.code(lesson.writing_task.target_phrase, language=None)
        answer = st.text_area(text(user, "answer"), key=f"writing:{day}", max_chars=2000)
        if st.button(text(user, "feedback"), disabled=not answer.strip() or future):
            result = attempt(
                user,
                lambda: generate(
                    "writing",
                    {
                        "text": answer,
                        "day": day,
                        "target_phrase": lesson.writing_task.target_phrase,
                        "sample_answer": lesson.writing_task.sample_answer,
                    },
                    user,
                ),
            )
            if result:
                st.session_state[f"writing_feedback:{day}"] = result
                repo.save_mistakes(user["id"], result.corrections)
                repo.save_step(user["id"], day, "writing", {"text": answer})
        if f"writing_feedback:{day}" in st.session_state:
            show_feedback(st.session_state[f"writing_feedback:{day}"])
        with st.expander(text(user, "sample")):
            st.write(lesson.writing_task.sample_answer)
            if st.button(text(user, "self_review"), disabled=not answer.strip() or future):
                mark("writing", {"text": answer, "self_review": True})
    with tabs[5]:
        with st.form(f"quiz:{day}"):
            answers = []
            for index, question in enumerate(lesson.mini_quiz):
                prompt = question.sentence_en or question.question_en or question.question_ko
                answers.append(
                    st.radio(
                        prompt,
                        range(len(question.options)),
                        format_func=lambda i, q=question: q.options[i],
                        index=None,
                        key=f"quiz:{day}:{index}",
                    )
                )
            submitted = st.form_submit_button(text(user, "check_quiz"), disabled=future)
        if submitted:
            if any(answer is None for answer in answers):
                st.warning(text(user, "complete_first"))
            else:
                score = sum(
                    answer == q.answer_index for answer, q in zip(answers, lesson.mini_quiz)
                )
                st.success(text(user, "quiz_result", score=score, total=len(answers)))
                for question in lesson.mini_quiz:
                    st.write(question.options[question.answer_index])
                    if user["language"] == "ko":
                        st.caption(question.explanation_ko)
                repo.save_step(user["id"], day, "quiz", {"score": score})
    with tabs[6]:
        reflection = st.text_area(
            text(user, "reflection_prompt"), key=f"reflection:{day}", max_chars=1000
        )
        if st.button(
            text(user, "mark"),
            key=f"mark:{day}:reflection",
            disabled=not reflection.strip() or future,
        ):
            mark("reflection", {"text": reflection})
    completed = any(row["day"] == day for row in repo.rows(db.completions, user["id"]))
    if completed:
        st.success(text(user, "completed"))
    elif st.button(text(user, "complete_lesson"), type="primary", disabled=future):
        if len(repo.completed_steps(user["id"], day)) < 7:
            st.warning(text(user, "complete_first"))
        else:
            repo.complete_lesson(user["id"], day, scheduled)
            st.rerun()
