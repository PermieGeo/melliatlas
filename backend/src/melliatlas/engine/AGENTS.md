# Engine Rules

Inherits root and backend guidance. This module owns **contracts, artifact semantics, registries, and DAG execution**, not tool policy or autonomous decisions.

- Keep Engine deterministic when supplied the same inputs, configuration, and recorded tool outputs. Do not import Agent, FastAPI, HTTP clients, ORM models, or concrete Sources/Analyzers.
- Define narrow typed `Source` / `Analyzer` capabilities and artifact envelopes; make input/output validation and schema versions explicit. Registries reject duplicate or incompatible registrations.
- Validate DAG dependencies before execution: unknown nodes, missing inputs, incompatible artifact types, and cycles fail with typed errors. Record per-node outcomes and dependency causality.
- Model provenance, data classification (`declared`, `observed`, `inferred`, `synthetic`), spatial reference/precision, coverage, freshness, and uncertainty explicitly. Missing evidence is not an empty-but-complete result.
- Bound execution by configured resource limits, deadlines, cancellation, and retries. Keep retry and idempotency decisions observable; do not assume a repeated operation is harmless.
- Test deterministic ordering/dependency behavior, cycles, type mismatches, cancellation, failures, partial outputs, and reproducibility with synthetic fixtures.
