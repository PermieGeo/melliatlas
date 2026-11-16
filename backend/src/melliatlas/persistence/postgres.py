"""Explicit optional Psycopg adapter for the persistence DB-API boundary."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, LiteralString

if TYPE_CHECKING:
    from psycopg import Connection, Cursor

from melliatlas.persistence.api import ConnectionFactory, DatabaseConnection, DatabaseCursor


class _PsycopgCursor:
    """Adapt Psycopg's generic cursor signature to the narrow store protocol."""

    def __init__(self, raw: "Cursor[tuple[object, ...]]") -> None:
        self._raw = raw

    def execute(self, query: LiteralString, params: Sequence[object] = ()) -> object:
        return self._raw.execute(query, params)

    def fetchone(self) -> tuple[object, ...] | None:
        return self._raw.fetchone()

    def close(self) -> None:
        self._raw.close()


class _PsycopgConnection:
    def __init__(self, raw: "Connection[tuple[object, ...]]") -> None:
        self._raw = raw

    def cursor(self) -> DatabaseCursor:
        return _PsycopgCursor(self._raw.cursor())

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def close(self) -> None:
        self._raw.close()


def connection_factory(dsn: str) -> ConnectionFactory:
    """Create short-lived connections only for explicitly configured local databases."""
    if not dsn.strip():
        raise ValueError("Region database DSN must not be empty")

    def connect() -> DatabaseConnection:
        from psycopg import connect as psycopg_connect
        from psycopg.rows import tuple_row

        return _PsycopgConnection(psycopg_connect(dsn, connect_timeout=5, row_factory=tuple_row))

    return connect
