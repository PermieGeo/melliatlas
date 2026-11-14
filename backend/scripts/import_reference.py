"""Validate a normalized reference snapshot without network or database writes."""

import argparse
import asyncio
import json
from pathlib import Path

from melliatlas.api.reference_loader import read_reference_documents, write_reference_report
from melliatlas.territories import InMemoryTerritoryCatalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an offline RU/BY reference snapshot")
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("independent_inventory", type=Path)
    args = parser.parse_args()
    snapshot, inventory = read_reference_documents(args.snapshot, args.independent_inventory)
    catalog = InMemoryTerritoryCatalog()
    asyncio.run(catalog.validate_reference(snapshot, inventory))
    print(json.dumps(write_reference_report(snapshot, inventory), sort_keys=True))


if __name__ == "__main__":
    main()
