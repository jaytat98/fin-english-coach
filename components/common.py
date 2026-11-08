import streamlit as st

from core.i18n import STRINGS, t
from core.llm import AIUnavailable
from core.speech import synthesize, transcribe


def text(user, key, **values):
    return t(key, user["language"], **values)


def attempt(user, action):
    try:
        with st.spinner(text(user, "loading")):
            return action()
    except (AIUnavailable, ValueError) as error:
        key = str(error) if str(error) in STRINGS else "error"
        st.error(text(user, key))
    except Exception:
        st.error(text(user, "error"))
    return None


def listen(user, sentence, key, voice="nova"):
    if st.button(text(user, "listen"), key=f"listen:{key}"):
        path = attempt(user, lambda: synthesize(sentence, voice, user["id"]))
        if path:
            st.audio(path.read_bytes(), format="audio/mp3")
        elif path is None:
            from core.config import get_settings

            if get_settings().fake_ai:
                st.info(text(user, "audio_demo"))


def audio_transcript(user, key, shadowing=False):
    recording = st.audio_input(text(user, "record"), key=f"record:{key}")
    if recording and st.button(text(user, "transcribe"), key=f"transcribe:{key}"):
        transcript = attempt(
            user, lambda: transcribe(recording.getvalue(), user["id"], shadowing=shadowing)
        )
        if transcript:
            st.session_state[f"transcript:{key}"] = transcript
    return st.text_area(text(user, "transcript"), key=f"transcript:{key}", max_chars=4000)


def show_feedback(result):
    st.write(result.message)
    if result.improved:
        st.success(result.improved)
    for correction in result.corrections:
        st.write(f"{correction.wrong} → {correction.right}")
        st.caption(correction.explanation)
