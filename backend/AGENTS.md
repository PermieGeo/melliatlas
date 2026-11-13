# Backend AGENTS.md

Extends `../AGENTS.md`. Applies to all `backend/` code and tests.

## Boundaries & Python
- **ALWAYS** keep one Python modular monolith: FastAPI API, independently executed worker, and explicit persistence adapters.
- **ALWAYS** restrict `api/` to input validation, authorization, transport, serialization, and error mapping. **NEVER** put domain decisions in routes.
- **ALWAYS** separate business capabilities; expose narrow typed interfaces and inject dependencies at composition boundaries.
- **NEVER** create global controller/service/repository layers, service locators, or implicit infrastructure dependencies.
- **ALWAYS** type public signatures; use strict pyright checks and Pydantic validation at untrusted boundaries.
- **NEVER** use unconstrained `Any`, unvalidated dictionaries, unchecked casts, or exception swallowing to bypass contracts.
- **ALWAYS** validate configuration, country profiles, provider permissions, model settings, and resource budgets server-side.
- **NEVER** read environment variables in domain code, hardcode provider/region selection, or commit secrets.
- **NEVER** block the event loop or launch fire-and-forget tasks for durable work.

## Engine — Typed Execution
- **ALWAYS** keep `engine/` runnable without Agent, LLM, HTTP, PostGIS, or provider connectivity when inputs are supplied.
- **NEVER** import `agent/`, FastAPI, ORM/SQL clients, or concrete Sources/Analyzers into Engine.
- **ALWAYS** define typed Source/Analyzer protocols, registries, versioned artifacts, and DAG execution in Engine.
- **ALWAYS** validate registrations, input compatibility, dependencies, and cycles before execution.
- **ALWAYS** preserve deterministic execution given identical inputs, configuration, and recorded external results.
- **ALWAYS** expose node status, causality, errors, partial results, cancellation, and configured time/resource limits.
- **NEVER** let Engine decide user goals, replan, or retry side effects without an explicit idempotency policy.
- **ALWAYS** carry source IDs, timestamps, CRS, precision, coverage, freshness, and uncertainty in artifacts.
- **NEVER** collapse `declared`, `observed`, `inferred`, and `synthetic` evidence or treat missing data as complete.

## Agent — Adaptive Planning
- **ALWAYS** implement observable `Goal -> Plan -> Execute -> Observe -> Evaluate -> Replan / Finish` behavior.
- **ALWAYS** choose tools from registered capabilities, authorized territories, prior observations, and the user goal.
- **ALWAYS** justify replanning with new evidence, conflicts, failures, or unmet prerequisites.
- **NEVER** disguise a fixed pipeline with decorative LLM calls; support a deterministic non-LLM planner.
- **ALWAYS** validate tool inputs and enforce limits on steps, calls, retries, time, context/tokens, and cost.
- **NEVER** execute model-supplied code, shell commands, unrestricted SQL/URLs, or unregistered tools.
- **NEVER** trust prompts, provider text, or model output as instructions or verified facts.
- **NEVER** disclose credentials, private apiary coordinates, or protected source records to unauthorized tools/models.
- **ALWAYS** record plan/tool versions, actions, evidence references, observations, decisions, and termination reasons.
- **ALWAYS** return an explicit incomplete/unavailable outcome when evidence or budgets are insufficient.

## Sources — Evidence Collection
- **ALWAYS** implement Engine-owned typed Source contracts; declare data kinds, geographic/time coverage, and access limits.
- **ALWAYS** select allowed providers from validated server-side country/territory profiles.
- **NEVER** invent unsupported upstream filters, data completeness, access permissions, or live coverage.
- **ALWAYS** isolate and explicitly label synthetic sources and outputs.
- **ALWAYS** verify access terms/licensing and restrict hosts, redirects, resolved IPs, payload size, request rate, and deadlines before real retrieval.
- **ALWAYS** enforce SSRF protection, bounded retries, cancellation, safe parsing, and idempotent ingestion.
- **ALWAYS** preserve permitted raw evidence, source identifiers, timestamps, versions, attribution, warnings, and prior review decisions.
- **NEVER** advance cache freshness or coverage after partial/failed collection or interpret source claims as verified events.

## Analyzers — Explainable Results
- **ALWAYS** declare typed inputs/outputs, dependencies, algorithm ID/version, limits, and geographic applicability.
- **ALWAYS** validate source provenance and input schemas; preserve evidence references, assumptions, and limitations in results.
- **NEVER** fetch providers, mutate original evidence, or perform Agent planning inside analyzers.
- **ALWAYS** keep deterministic geospatial/statistical logic testable without network or LLM access.
- **ALWAYS** specify CRS, axis order, units, geometry validity, precision, and proper distance/area operations.
- **NEVER** fabricate observations, pesticide-safety conclusions, calibrated confidence, or completeness from missing evidence.

## Jobs, Persistence & Errors
- **ALWAYS** persist job state, checkpoints, retries, idempotency keys, and results before claiming durability/restart safety.
- **ALWAYS** use explicit transactions, parameterized SQL, reviewable migrations, and PostGIS spatial operations where applicable.
- **ALWAYS** separate domain errors from HTTP codes and sanitize public error details.
- **NEVER** log secrets, exact private apiary locations, or sensitive untrusted source payloads.

## Backend Verification
- **ALWAYS** use deterministic pytest fixtures, controlled clocks, seeded randomness, and fake Sources/Analyzers in routine tests.
- **NEVER** require live providers, production credentials, model APIs, or uncontrolled sleeps in routine tests.
- **ALWAYS** test DAG cycles, type mismatches, dependency failure, cancellation, limits, partial results, and provenance.
- **ALWAYS** compare Agent decisions with a fixed pipeline on the same synthetic scenario; verify justified replanning and inconclusive outcomes.
- **ALWAYS** test Source schema drift, empty/partial pages, duplicates, rate limits, redirects, retries, and failed collection.
- **ALWAYS** use real PostGIS for spatial SQL, migrations, access constraints, transactions, and recovery tests when implemented.
- **NEVER** claim mock-only tests prove PostGIS correctness or worker restart safety.
- **ALWAYS** run available Ruff, pyright, pytest, architecture, and build checks; report unavailable checks accurately.
