# Saturn Offline Provider Parser

`api.py` exports the bounded, source-specific offline normalization and pagination
contract. `legacy_treatment.py` parses the historically observed Russia-only
`/planapplybees` JSON shape, `geometry.py` validates optional WGS84 geometry, and
`pagination.py` checks page progress. `sources/notices.py` owns generic notice DTOs.

The parser consumes supplied payloads, performs no I/O and has no implied current
permission to contact Saturn. Unknown or invalid geometry and missing schedules stay
unknown; no source observation guarantees spraying occurred or that an apiary is safe.
Real transport, access rights, provenance and persistent source snapshots require a
separate approved feature. The previous `sources/saturn.py` facade is retired; callers
use `sources.providers.saturn.api` for provider-specific operations.
