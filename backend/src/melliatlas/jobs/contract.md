# Investigation Jobs Contract — V01

`InvestigationService` provides `submit`, `get` and `process` operations. `InMemoryInvestigationService` stores immutable snapshot values in a lock-protected mapping per application instance; a new process or app instance has an empty store. A successful `submit` validates the fixed scenario and date window **before** inserting `QUEUED` state. `process` transitions through `RUNNING` to terminal `COMPLETED` or `FAILED` and does not mutate a terminal snapshot again.

`InvestigationOutcomeKind` reports domain suitability separately from execution `InvestigationStatus`. Insufficient fixture evidence is `COMPLETED/INSUFFICIENT_EVIDENCE`, not `FAILED`. Unexpected calculation failures are logged and surfaced only as a sanitized `FAILED` diagnostic. No restart recovery, database transaction, automatic retries, deduplication or cross-worker synchronization is claimed. Production persistence and immutable historical reopening are reserved for V02.
