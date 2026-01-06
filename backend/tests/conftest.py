"""Shared pytest fixtures for backend tests."""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base
from backend.models.runs import Run
from backend.models.tasks import Task


import pytest_asyncio


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """Create an in-memory SQLite database session for testing."""
    from datetime import datetime, timezone
    import uuid

    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")

    # SQLite doesn't have a now() function like PostgreSQL, so we need to replace it
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @event.listens_for(engine.sync_engine, "before_execute")
    def replace_now(conn, clauseelement, multiparams, params):
        """Replace PostgreSQL now() with SQLite datetime('now')"""
        if hasattr(clauseelement, "text") and "now()" in str(clauseelement):
            clauseelement.text = clauseelement.text.replace("now()", "datetime('now')")
        return clauseelement, multiparams, params

    # Handle server defaults in DDL
    @event.listens_for(Base.metadata, "before_create")
    def replace_now_in_ddl(target, connection, **kw):
        """Replace now() in server defaults during table creation"""
        for table in target.tables.values():
            for column in table.columns:
                if column.server_default is not None and hasattr(column.server_default, "text"):
                    if "now()" in column.server_default.text:
                        column.server_default.text = column.server_default.text.replace(
                            "now()", "datetime('now')"
                        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()
    os.unlink(path)
