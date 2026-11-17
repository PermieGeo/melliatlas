"""Territory module public adapter exports."""

from .catalog import InMemoryTerritoryCatalog
from .countries import supported_countries

__all__ = ["InMemoryTerritoryCatalog", "supported_countries"]
