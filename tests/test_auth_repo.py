import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from core import auth, db, repo
from core.rate_limit import reserve


def test_login_session_expiry_and_revocation(learner):
    assert auth.login(learner["email"], "wrong") is None
    token = auth.login(learner["email"], "a-secure-password")
    assert auth.resolve_session(token)["id"] == learner["id"]
    with db.get_engine().begin() as connection:
        row = connection.execute(select(db.sessions)).mappings().one()
        assert row["token_hash"] == hashlib.sha256(token.encode()).hexdigest()
        assert token not in str(dict(row))
        expiry = datetime.fromisoformat(row["expires_at"])
        assert timedelta(days=13) < expiry - datetime.now(UTC) <= timedelta(days=14)
        connection.execute(
            update(db.sessions).values(
                expires_at=(datetime.now(UTC) - timedelta(seconds=1)).isoformat()
            )
        )
    assert auth.resolve_session(token) is None
    token = auth.issue_session(learner["id"])
    auth.logout(token)
    assert auth.resolve_session(token) is None


def test_share_link_removes_secrets():
    assert auth.share_url("https://example.streamlit.app/path?s=secret&other=private#token") == (
        "https://example.streamlit.app/path"
    )
    with pytest.raises(ValueError):
        auth.share_url("javascript:alert(1)")


def test_user_isolation_and_cascading_deletion(learner):
    other = auth.create_user(
        "other@example.test", "a-secure-password", "Other", "Tax", "Manager", "ko", "test-code"
    )
    repo.add_card(learner["id"], "phrase:1", "phrase", "meaning")
    repo.add_card(other["id"], "phrase:1", "other phrase", "meaning")
    token = auth.issue_session(learner["id"])
    repo.save_step(learner["id"], 1, "phrase", {})
    repo.visit(learner["id"])
    repo.delete_user(learner["id"])
    assert auth.resolve_session(token) is None
    assert repo.rows(db.progress, learner["id"]) == []
    assert repo.rows(db.reviews, learner["id"]) == []
    assert len(repo.rows(db.reviews, other["id"])) == 1


def test_completion_requires_all_steps_and_is_idempotent(learner):
    user_id = learner["id"]
    with pytest.raises(ValueError):
        repo.complete_lesson(user_id, 1, repo.today())
    for step in ("phrase", "terms", "tip", "speaking", "writing", "quiz", "reflection"):
        repo.save_step(user_id, 1, step, {})
        repo.save_step(user_id, 1, step, {})
    repo.complete_lesson(user_id, 1, repo.today())
    repo.complete_lesson(user_id, 1, repo.today())
    assert len(repo.rows(db.progress, user_id)) == 7
    assert len(repo.rows(db.completions, user_id)) == 1
    assert repo.rows(db.completions, user_id)[0]["on_time"] == 1


def test_daily_limit(learner):
    reserve(learner["id"], "ai", 2)
    reserve(learner["id"], "ai", 2)
    with pytest.raises(ValueError, match="daily_limit"):
        reserve(learner["id"], "ai", 2)
    assert repo.rows(db.limits, learner["id"])[0]["count"] == 2


def test_passwords_use_different_salts():
    first = auth.hash_password("a password")
    second = auth.hash_password("a password")
    assert first != second
    assert auth.verify_password("a password", first)
    assert not auth.verify_password("different", first)
