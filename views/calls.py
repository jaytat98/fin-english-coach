from uuid import uuid4

import streamlit as st

from components.common import attempt, audio_transcript, listen, text
from core import db, repo
from core.config import get_settings
from core.content import load_scenarios
from core.llm import generate
from core.rate_limit import reserve
from core.scoring import call_overall_score


def render(user):
    st.title(text(user, "calls"))
    st.caption(text(user, "privacy"))
    active = st.session_state.get("active_call")
    if not active:
        tab1, tab2 = st.tabs([text(user, "library"), text(user, "rehearsal")])
        scenarios = load_scenarios()
        with tab1:
            selected = st.selectbox(
                text(user, "scenario"),
                scenarios,
                format_func=lambda s: s.title_ko if user["language"] == "ko" else s.title_en,
            )
        with tab2:
            brief = st.text_area(text(user, "brief"), max_chars=2000)
            if get_settings().fake_ai:
                st.info(text(user, "rehearsal_demo"))
            if st.button(text(user, "build"), disabled=not brief.strip()):
                result = attempt(
                    user,
                    lambda: generate(
                        "custom_scenario",
                        {
                            "text": brief,
                            "service_line": user["service_line"],
                        },
                        user,
                    ),
                )
                if result:
                    st.session_state["rehearsal_scenario"] = result.scenario
            if "rehearsal_scenario" in st.session_state:
                custom = st.session_state["rehearsal_scenario"]
                st.write(custom.title_ko if user["language"] == "ko" else custom.title_en)
                if st.button(text(user, "start_call"), key="start_rehearsal"):
                    start(user, custom)
        with tab1:
            if user["language"] == "ko":
                st.write(selected.briefing_ko)
            st.subheader(text(user, "goals"))
            for goal in selected.goals:
                st.write("• " + (goal.text_ko if user["language"] == "ko" else goal.text_en))
            if st.button(text(user, "start_call"), type="primary"):
                start(user, selected)
        return
    scenario = active["scenario"]
    st.subheader(scenario.title_ko if user["language"] == "ko" else scenario.title_en)
    for turn in active["transcript"]:
        with st.chat_message("user" if turn["role"] == "user" else "assistant"):
            st.write(turn["content"])
    last_assistant = next(
        turn for turn in reversed(active["transcript"]) if turn["role"] == "assistant"
    )
    speaker = next(
        (p for p in scenario.personas if p.name == last_assistant.get("speaker")),
        scenario.personas[0],
    )
    listen(user, last_assistant["content"], f"call:{active['id']}:{active['turns']}", speaker.voice)
    if not active.get("evaluation"):
        if active.get("pending"):
            st.info(text(user, "loading"))
            if st.button(text(user, "send"), key="retry_turn"):
                next_turn(user, active)
        elif not active.get("finished"):
            if st.button(text(user, "hint")):
                active["hints"] += 1
                st.info(scenario.key_phrases[(active["hints"] - 1) % len(scenario.key_phrases)].en)
            reply = audio_transcript(user, f"call:{active['id']}:{active['turns']}")
            if st.button(text(user, "send"), disabled=not reply.strip()):
                active["transcript"].append({"role": "user", "content": reply})
                active["turns"] += 1
                if active["turns"] >= scenario.max_turns:
                    active["finished"] = True
                    st.rerun()
                active["pending"] = True
                next_turn(user, active)
        if active["turns"] and st.button(text(user, "end_call"), type="primary"):
            result = attempt(
                user,
                lambda: generate(
                    "call_evaluator",
                    {
                        "scenario": scenario.model_dump(by_alias=True),
                        "transcript": active["transcript"],
                    },
                    user,
                ),
            )
            if result:
                said = " ".join(
                    t["content"].casefold() for t in active["transcript"] if t["role"] == "user"
                )
                phrases = sum(p.en.casefold().rstrip(".") in said for p in scenario.key_phrases)
                score = call_overall_score(
                    result.scores.model_dump(),
                    active["hints"],
                    phrases,
                    scenario.call_type == "voicemail",
                )
                repo.save_call(
                    user["id"],
                    active["id"],
                    scenario.id,
                    score,
                    active["transcript"],
                    result,
                    get_settings().fake_ai,
                )
                repo.save_mistakes(user["id"], result.corrections)
                active["evaluation"], active["score"] = result, score
                st.rerun()
    else:
        st.metric(text(user, "score"), f"{active['score']} / 100")
        st.write(active["evaluation"].summary)
        st.info(active["evaluation"].next_step)
    if st.button(text(user, "reset_call")):
        del st.session_state["active_call"]
        st.rerun()


def start(user, scenario):
    def action():
        reserve(user["id"], "mock_calls", get_settings().limits.mock_calls_per_day)
        st.session_state["active_call"] = {
            "id": uuid4().hex,
            "scenario": scenario,
            "hints": 0,
            "turns": 0,
            "transcript": [
                {
                    "role": "assistant",
                    "content": scenario.personas[0].opening_line,
                    "speaker": scenario.personas[0].name,
                }
            ],
        }
        return True

    if attempt(user, action):
        st.rerun()


def next_turn(user, active):
    scenario = active["scenario"]
    patterns = [
        row["pattern_key"] for row in repo.rows(db.mistakes, user["id"]) if not row["resolved"]
    ][:3]
    result = attempt(
        user,
        lambda: generate(
            "call_turn",
            {
                "scenario": scenario.model_dump(by_alias=True),
                "transcript": active["transcript"][-get_settings().limits.chat_history_messages :],
                "pattern_keys": patterns,
            },
            user,
        ),
    )
    if result:
        active["transcript"].append(
            {"role": "assistant", "content": result.text, "speaker": result.speaker}
        )
        active["pending"] = False
        active["finished"] = result.finished
        st.rerun()
