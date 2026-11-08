"""Isolated temporary databases; no test calls a real AI service."""

import pytest

from core import config, db


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr(
        config,
        "_read",
        lambda name, default=None: {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
            "FAKE_AI": "1",
            "PILOT_ACCESS_CODE": "test-code",
            "ADMIN_PASSWORD": "test-admin",
            "PROGRAM_START_DATE": "2026-11-02",
        }.get(name, default),
    )
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()
    db.engine_for.cache_clear()


@pytest.fixture
def learner(storage):
    from core.auth import create_user

    return create_user(
        "learner@example.test", "a-secure-password", "Learner", "Audit", "Senior", "en", "test-code"
    )
