# Specification Rules

Inherits `../../AGENTS.md`. No normative specification has been approved in this new repository.

- Write **English** requirements describing observable behavior, purpose, actors, scope/non-goals, failure/boundary cases, security, and independently testable acceptance criteria. Keep implementation tactics out of normative requirements.
- Use explicit stable requirement, stage, and test IDs. Distinguish approved scope, provisional choices, synthetic fixtures, source claims, and verified implementations.
- Every created or materially changed **sub-spec** must have a separate, linked, detailed **advisory implementation plan** in the same handoff. Include ordered changes by verified/proposed file, dependencies, error/retry/restart, migrations, test commands, and acceptance evidence.
- Compare meaningful design alternatives before fixing consequential framework, model, provider, or data-contract choices. Prefer simple extension points over speculative systems.
- Do not claim a draft is approved, invent completed stages, or change developer-owned workflow state and acceptance checkpoints. Archive a sub-spec **with its plan** only after explicit developer approval.
- Keep this index, active specs, plans, and actual code ownership consistent. Never import `melliatlas_v01` requirements or status wholesale.
