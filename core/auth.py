"""Password hashing and revocable, hashed session links with 14-day expiry."""

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from sqlalchemy import delete, select

from core import db
from core.config import LEVELS, SERVICE_LINES, UI_LANGS, get_settings

SESSION_DAYS = 14


def now() -> str:
    return datetime.now(UTC).isoformat()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or not 100_000 <= int(iterations) <= 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), int(iterations)
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_user(email, password, name, service_line, level, language, access_code):
    settings = get_settings()
    if not settings.pilot_access_code or not hmac.compare_digest(
        access_code.encode(), settings.pilot_access_code.encode()
    ):
        raise ValueError("access_code")
    email = email.strip().casefold()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
        raise ValueError("invalid_email")
    if len(password) < 10 or len(password) > 256:
        raise ValueError("password_length")
    if not name.strip() or len(name) > 80:
        raise ValueError("invalid_name")
    if service_line not in SERVICE_LINES or level not in LEVELS or language not in UI_LANGS:
        raise ValueError("invalid_profile")
    user = dict(
        id=uuid4().hex,
        email=email,
        name=name.strip(),
        password_hash=hash_password(password),
        service_line=service_line,
        level=level,
        language=language,
        created_at=now(),
        start_date=settings.program_start_date.isoformat(),
    )
    with db.get_engine().begin() as connection:
        connection.execute(db.users.insert().values(**user))
    return user


def issue_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    with db.get_engine().begin() as connection:
        connection.execute(delete(db.sessions).where(db.sessions.c.expires_at <= now()))
        connection.execute(
            db.sessions.insert().values(
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                user_id=user_id,
                expires_at=(datetime.now(UTC) + timedelta(days=SESSION_DAYS)).isoformat(),
            )
        )
    return token


def login(email: str, password: str) -> str | None:
    with db.get_engine().connect() as connection:
        user = (
            connection.execute(select(db.users).where(db.users.c.email == email.strip().casefold()))
            .mappings()
            .first()
        )
    if user and verify_password(password, user["password_hash"]):
        return issue_session(user["id"])
    # Keep a meaningful password-hashing cost for unknown accounts as well.
    if not user:
        hash_password(password[:256])
    return None


def resolve_session(token: str) -> dict | None:
    if not token or len(token) > 128:
        return None
    with db.get_engine().connect() as connection:
        user = (
            connection.execute(
                select(db.users)
                .join(db.sessions, db.users.c.id == db.sessions.c.user_id)
                .where(
                    db.sessions.c.token_hash == hashlib.sha256(token.encode()).hexdigest(),
                    db.sessions.c.expires_at > now(),
                )
            )
            .mappings()
            .first()
        )
    return dict(user) if user else None


def logout(token: str) -> None:
    with db.get_engine().begin() as connection:
        connection.execute(
            delete(db.sessions).where(
                db.sessions.c.token_hash == hashlib.sha256(token.encode()).hexdigest()
            )
        )


def share_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError("APP_URL must be an http(s) URL")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
