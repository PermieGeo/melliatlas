# Source Adapter Rules

Inherits root and backend guidance. Sources **retrieve and normalize evidence**; they do not decide whether a location is safe.

- Implement Engine's declared source protocol; advertise supported data kinds, geographic/time filters, access constraints, rate limits, and provenance capabilities. Never infer unsupported provider filters.
- Select actual providers through server-side country/territory configuration, never client toggles or hardcoded region IDs. Synthetic providers must be labeled and isolated from live records.
- Check legal access, licensing, attribution, allowed hosts, redirects/DNS/IP, payload size, rate limits, deadlines, and retries before connecting to real endpoints. No production fetch enabled without verified source permission and contract tests.
- Preserve immutable source snapshots where permitted, acquisition/publication timestamps, stable external IDs, retrieval status, and parse warnings. Deduplicate idempotently without destroying version history.
- Fail visibly on malformed data, partial coverage, invalid geometries, changing pages, 429/503, or missing evidence. Cache freshness must not advance on a partial import.
- Test using captured **permitted** fixtures and deterministic fakes; never depend on a live upstream service in the standard suite.
