# Specification AGENTS.md

Inherits `../../AGENTS.md`. New MelliAtlas specifications begin from an empty, unapproved SDD state.

## Requirements
- **ALWAYS** write normative specs, advisory plans, and repository documentation in English.
- **ALWAYS** state actors, scope, non-goals, requirements, observable acceptance criteria, security, failures, and boundaries.
- **ALWAYS** use stable requirement, stage, and test IDs linked to owning modules.
- **ALWAYS** distinguish approved requirements, drafts, planned behavior, synthetic examples, and verified implementation.
- **NEVER** turn a discussion draft or `melliatlas_v01` history into an approved requirement implicitly.
- **NEVER** prescribe implementation tactics as normative behavior unless they are genuine constraints.

## Implementation Plans
- **ALWAYS** deliver a separate linked advisory implementation plan with each new or materially revised sub-spec.
- **ALWAYS** specify ordered stages, verified/proposed file paths, responsibilities, dependencies, data changes, and migrations.
- **ALWAYS** specify failure/retry/restart/rollback, independent tests, executable commands where verified, and acceptance evidence.
- **NEVER** invent existing files, implemented APIs, completed checks, or developer approvals.
- **NEVER** replace evidence-based design choices with speculative platforms or frameworks.

## State & Lifecycle
- **ALWAYS** keep spec index, active requirements, linked plans, and implemented interfaces consistent.
- **NEVER** advance developer-controlled checkpoints or archive a sub-spec without explicit approval.
- **ALWAYS** archive an approved completed sub-spec together with its linked plan.
