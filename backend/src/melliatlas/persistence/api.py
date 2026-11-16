"""Public DB-API typing ports used by injected PostgreSQL persistence adapters.

The jobs capability owns the CompletedInvestigationStore Protocol; PostGIS SQL,
connection lifecycle and snapshot serialization stay in postgis_store.py.
"""

from collections.abc import Callable, Sequence
from typing import LiteralString, Protocol


class DatabaseCursor(Protocol):
    def execute(self, query: LiteralString, params: Sequence[object] = ()) -> object: ...
    def fetchone(self) -> tuple[object, ...] | None: ...
    def close(self) -> None: ...


class DatabaseConnection(Protocol):
    def cursor(self) -> DatabaseCursor: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


ConnectionFactory = Callable[[], DatabaseConnection]

__all__ = ["DatabaseCursor", "DatabaseConnection", "ConnectionFactory"]
