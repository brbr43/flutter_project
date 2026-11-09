"""Async SQLAlchemy engine / session helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base
from app.paths import ensure_runtime_dirs

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

# Additive Phase 4 columns for DBs created in Phase 3 (SQLite has no ALTER IF NOT EXISTS).
_PHASE4_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "projects": [
        ("idea", "TEXT DEFAULT '' NOT NULL"),
        ("genre", "VARCHAR(40) DEFAULT 'drama' NOT NULL"),
        ("true_story_mode", "BOOLEAN DEFAULT 0 NOT NULL"),
        ("script_title", "VARCHAR(300) DEFAULT '' NOT NULL"),
        ("synopsis", "TEXT DEFAULT '' NOT NULL"),
        ("beats", "JSON"),
        ("generator", "VARCHAR(40) DEFAULT 'template' NOT NULL"),
        ("story_meta", "JSON"),
    ],
    "scenes": [
        ("camera", "TEXT DEFAULT '' NOT NULL"),
        ("lighting", "TEXT DEFAULT '' NOT NULL"),
        ("beat_id", "VARCHAR(80) DEFAULT '' NOT NULL"),
        ("content_tag", "VARCHAR(40) DEFAULT 'fiction' NOT NULL"),
        ("duration_hint_sec", "INTEGER DEFAULT 5 NOT NULL"),
        ("meta", "JSON"),
    ],
}


def get_engine():
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        ensure_runtime_dirs(settings)
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def _existing_columns(sync_conn, table: str) -> set[str]:
    rows = sync_conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}


def _migrate_phase4(sync_conn) -> None:
    for table, cols in _PHASE4_COLUMNS.items():
        try:
            existing = _existing_columns(sync_conn, table)
        except Exception:  # noqa: BLE001 — table may not exist yet
            continue
        if not existing:
            continue
        for name, decl in cols:
            if name in existing:
                continue
            sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {decl}"))


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_phase4)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def reset_engine() -> None:
    """Test helper — dispose and clear singleton (e.g. after STORYVERSE_ROOT change)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
