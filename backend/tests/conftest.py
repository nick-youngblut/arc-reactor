"""Shared pytest fixtures for backend tests."""

import os
import tempfile

import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """Create an in-memory SQLite database session for testing."""
    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")

    # SQLite doesn't have a now() function like PostgreSQL, so we need to replace it
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @event.listens_for(engine.sync_engine, "before_execute", retval=True)
    def replace_postgres_functions(conn, clauseelement, multiparams, params, execution_options):
        """Replace PostgreSQL functions with SQLite equivalents"""
        # Convert to string and replace
        sql = str(clauseelement)
        modified = False

        if "now()" in sql:
            sql = sql.replace("now()", "datetime('now')")
            modified = True

        if modified:
            return sql, multiparams, params
        return clauseelement, multiparams, params

    # Handle server defaults in DDL
    @event.listens_for(Base.metadata, "before_create")
    def replace_postgres_defaults_in_ddl(target, connection, **kw):
        """Replace PostgreSQL server defaults during table creation for SQLite"""
        for table in target.tables.values():
            for column in table.columns:
                if column.server_default is not None and hasattr(column.server_default, "arg"):
                    arg = column.server_default.arg
                    if hasattr(arg, "text"):
                        # Replace now() with SQLite equivalent
                        if "now()" in arg.text:
                            arg.text = arg.text.replace("now()", "datetime('now')")
                        # Remove gen_random_uuid() - not needed for remaining tests
                        if "gen_random_uuid()" in arg.text:
                            column.server_default = None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()
    os.unlink(path)
