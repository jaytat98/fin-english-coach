"""Real Streamlit widget flows with a temporary database and FAKE_AI only."""

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from core import auth, db, repo


def button(app, label):
    return next(item for item in app.button if item.label == label)


def demo_app():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py", default_timeout=20
    ).run()
    assert not app.exception
    button(app, "Explore the demo").click().run()
    assert not app.exception
    return app


def test_all_pages_render_in_fake_mode(storage):
    app = demo_app()
    for page in ("today", "calls", "review", "ask", "mistakes", "roadmap", "records", "admin"):
        app.radio(key="navigation").set_value(page).run()
        assert not app.exception, page
    app.text_input[0].set_value("test-admin")
    button(app, "Sign in as admin").click().run()
    assert not app.exception
    assert len(app.metric) == 6


def test_lesson_review_and_call_roundtrip(storage):
    app = demo_app()
    app.selectbox[0].set_value(1).run()
    for step in ("phrase", "terms", "tip"):
        app.button(key=f"mark:1:{step}").click().run()
        assert not app.exception
    app.text_area(key="transcript:speaking:1").set_value("Let's circle back tomorrow.").run()
    button(app, "Compare sentences").click().run()
    app.text_area(key="writing:1").set_value("Let's circle back after the meeting.").run()
    button(app, "Get feedback").click().run()
    app.radio(key="quiz:1:0").set_value(1)
    app.radio(key="quiz:1:1").set_value(0)
    button(app, "Check answers").click().run()
    app.text_area(key="reflection:1").set_value("I will use it in a meeting.").run()
    app.button(key="mark:1:reflection").click().run()
    button(app, "Finish this lesson").click().run()
    assert not app.exception
    assert len(repo.rows(db.completions, "demo-learner")) == 1
    assert len(repo.rows(db.reviews, "demo-learner")) == 4
    app.radio(key="navigation").set_value("review").run()
    button(app, "Reveal answer").click().run()
    button(app, "Good").click().run()
    assert any(
        json.loads(row["state"])["reps"] == 1 for row in repo.rows(db.reviews, "demo-learner")
    )
    app.radio(key="navigation").set_value("calls").run()
    button(app, "Start call").click().run()
    app.text_area[0].set_value(
        "We finished revenue testing. Can you help with the confirmation?"
    ).run()
    button(app, "Send").click().run()
    button(app, "End call and get feedback").click().run()
    assert not app.exception
    calls = repo.rows(db.calls, "demo-learner")
    assert len(calls) == 1 and calls[0]["fake"] == 1
    assert calls[0]["score"] == 70


def test_logout_and_account_deletion_revoke_session(storage):
    app = demo_app()
    token = app.query_params["s"][0]
    app.radio(key="navigation").set_value("records").run()
    app.checkbox[0].check().run()
    button(app, "Delete account and data").click().run()
    assert not app.exception
    assert auth.resolve_session(token) is None
    assert button(app, "Sign in")
