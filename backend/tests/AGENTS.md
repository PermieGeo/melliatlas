# Backend Test Rules

Inherits root and backend guidance. Test public behavior and invariants, not private function arrangements.

- Prefer fast pytest unit tests with typed fixtures; use seeded randomness, frozen clocks, deterministic fake Sources/Analyzers and recorded Agent decisions.
- Verify DAG type/dependency checks, duplicate IDs, error propagation, bounded retries, cancellation, resource limits, idempotency, and evidence/provenance integrity.
- Verify **adaptive** behavior separately from a fixed pipeline: ambiguous intermediate evidence must trigger a justified further action or an explicitly inconclusive outcome.
- Run real PostGIS integration tests for geospatial queries, migrations, transactions, privacy and restart semantics when those modules exist. A mocked database does not prove storage correctness.
- Do not require live providers, model APIs, real credentials, or nondeterministic wall-clock waits. Label synthetic expectations unambiguously.
- Do not disable legitimate tests or relax assertions to mask a regression. Report checks actually executed and environment-dependent gaps.
