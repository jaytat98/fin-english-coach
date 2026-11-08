"""Portable SQLAlchemy storage for SQLite demos and PostgreSQL deployments."""

from functools import lru_cache
from pathlib import Path

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    text,
)
from sqlalchemy.engine import make_url

from core.config import get_settings

metadata = MetaData()
users = Table(
    "users",
    metadata,
    Column("id", String, primary_key=True),
    Column("email", String, unique=True, nullable=False),
    Column("name", String, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("service_line", String, nullable=False),
    Column("level", String, nullable=False),
    Column("language", String, nullable=False),
    Column("created_at", String, nullable=False),
    Column("start_date", String, nullable=False),
)


def owner():
    return Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


sessions = Table(
    "sessions",
    metadata,
    Column("token_hash", String, primary_key=True),
    owner(),
    Column("expires_at", String, nullable=False),
)
progress = Table(
    "lesson_progress",
    metadata,
    owner(),
    Column("day", Integer, nullable=False),
    Column("step", String, nullable=False),
    Column("payload", Text, nullable=False),
    Column("created_at", String, nullable=False),
    UniqueConstraint("user_id", "day", "step"),
)
completions = Table(
    "lesson_completions",
    metadata,
    owner(),
    Column("day", Integer, nullable=False),
    Column("completed_date", String, nullable=False),
    Column("on_time", Integer, nullable=False),
    UniqueConstraint("user_id", "day"),
)
calls = Table(
    "calls",
    metadata,
    Column("id", String, primary_key=True),
    owner(),
    Column("scenario_id", String, nullable=False),
    Column("score", Integer, nullable=False),
    Column("transcript", Text, nullable=False),
    Column("feedback", Text, nullable=False),
    Column("created_at", String, nullable=False),
    Column("fake", Integer, nullable=False),
)
reviews = Table(
    "reviews",
    metadata,
    owner(),
    Column("card_id", String, nullable=False),
    Column("front", Text, nullable=False),
    Column("back", Text, nullable=False),
    Column("state", Text, nullable=False),
    UniqueConstraint("user_id", "card_id"),
)
mistakes = Table(
    "mistakes",
    metadata,
    Column("id", String, primary_key=True),
    owner(),
    Column("pattern_key", String, nullable=False),
    Column("wrong", Text, nullable=False),
    Column("right", Text, nullable=False),
    Column("note", Text, nullable=False),
    Column("resolved", Integer, nullable=False, default=0),
    Column("created_at", String),
)
usage = Table(
    "ai_usage",
    metadata,
    Column("id", String, primary_key=True),
    owner(),
    Column("operation", String, nullable=False),
    Column("model", String, nullable=False),
    Column("cost", Float, nullable=False),
    Column("created_at", String, nullable=False),
    Column("fake", Integer, nullable=False),
)
limits = Table(
    "daily_limits",
    metadata,
    owner(),
    Column("day", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("count", Integer, nullable=False),
    UniqueConstraint("user_id", "day", "kind"),
)
visits = Table(
    "visits",
    metadata,
    owner(),
    Column("day", String, nullable=False),
    UniqueConstraint("user_id", "day"),
)
feedback = Table(
    "feedback",
    metadata,
    Column("id", String, primary_key=True),
    owner(),
    Column("rating", Integer, nullable=False),
    Column("message", Text, nullable=False),
    Column("created_at", String, nullable=False),
)


@lru_cache(maxsize=4)
def engine_for(url: str):
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite" and parsed.database not in (None, "", ":memory:"):
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    options = {"pool_pre_ping": True}
    if parsed.get_backend_name() == "sqlite":
        options["connect_args"] = {"check_same_thread": False, "timeout": 30}
    elif parsed.drivername == "postgresql+psycopg":
        # Supabase's shared transaction pooler cannot retain prepared statements.
        options["connect_args"] = {"prepare_threshold": None}
        options.update(pool_size=2, max_overflow=2)
    engine = create_engine(url, **options)
    if parsed.get_backend_name() == "sqlite":

        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    metadata.create_all(engine)
    if parsed.get_backend_name() == "postgresql":
        # Supabase exposes public-schema tables through its Data API. Learners
        # access data only through this server, never through anonymous DB roles.
        with engine.begin() as connection:
            for table in metadata.sorted_tables:
                connection.execute(text(f'ALTER TABLE "{table.name}" ENABLE ROW LEVEL SECURITY'))
    return engine


def get_engine():
    return engine_for(get_settings().database_url)


def insert_once(connection, table, values, conflict_columns):
    """Atomic idempotent writes supported by both deployment database engines."""
    if connection.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    statement = (
        insert(table).values(**values).on_conflict_do_nothing(index_elements=conflict_columns)
    )
    return connection.execute(statement)
