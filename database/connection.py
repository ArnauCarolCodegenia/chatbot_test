"""
Database connection and session service factory.

Supports SQLite (local dev) and PostgreSQL/MySQL (production).
The DATABASE_URL env var controls which backend is used.

ADK's DatabaseSessionService stores conversation sessions and state in the DB,
enabling persistent, cross-restart memory for agents.

Session backend is selected by the SESSION_BACKEND env var:
  memory   → InMemorySessionService (default, lost on restart)
  database → DatabaseSessionService (persistent)
"""

from __future__ import annotations

import logging
import os

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None


def get_async_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./adk_project.db")
        _engine = create_async_engine(url, echo=False, future=True)
        logger.info("Database engine created: %s", url.split("@")[-1])
    return _engine


def build_session_service():
    """
    Return the session service configured via SESSION_BACKEND env var.

    memory   → sessions live in RAM (fast, no persistence)
    database → sessions persisted in SQL (recommended for production)
    """
    backend = os.getenv("SESSION_BACKEND", "memory").lower()

    if backend == "database":
        from google.adk.sessions import DatabaseSessionService
        engine = get_async_engine()
        logger.info("Using DatabaseSessionService")
        return DatabaseSessionService(db_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./adk_project.db"))

    from google.adk.sessions import InMemorySessionService
    logger.info("Using InMemorySessionService")
    return InMemorySessionService()


async def create_tables() -> None:
    """Create all ORM tables. Call once at startup."""
    from database.models import Base
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified.")
