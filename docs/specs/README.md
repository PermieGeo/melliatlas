# MelliAtlas Specification Index

## Product-level specification

- [Umbrella Specification](umbrella.md) — the product mission, cross-cutting requirements, stage sequence, and acceptance outcomes. **Draft; pending developer approval.**

## Stage lifecycle

No stage-specific normative sub-specification or implementation plan has been selected or created yet. `active/` contains only scaffolding, and `archive/` contains no completed stage documents. `STATE.json` will be initialized when the first workstream is explicitly selected; do not fabricate an active checkpoint.

For a selected stage:

1. Write an active normative sub-spec with stable requirement IDs, scope, boundary and failure cases, and independently verifiable outcomes.
2. Create its **separate linked implementation plan** with proposed file changes and test-first steps; do not prepare plans for unselected stages.
3. Obtain developer approval before implementation. Successful tests and commits do not automatically advance the checkpoint.
4. After completed implementation and explicit acceptance, archive the sub-spec and linked plan together, then update references and the developer-controlled state.

Feature identifiers and short descriptions belong in [`docs/FEATURES.md`](../FEATURES.md); specification, implementation, and test links belong in [`feature-cross-ref.yaml`](feature-cross-ref.yaml). Validate the checkpoint against [`state.schema.json`](state.schema.json) when initialized.
