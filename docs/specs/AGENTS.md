# Specification Engineering Guidance

Extends `../../AGENTS.md`. These are repository SDD maintenance rules; source files, repository comments and documentation remain in English.

## Authority and ownership

- The umbrella spec owns the roadmap. Only an explicitly developer-authorized task within the selected workstream permits implementation. Requirements approval, task authorization, completed verification and developer acceptance are separate decisions.
- Preserve stable requirement, acceptance, feature and task IDs. Do not mark work complete from an archive, generated patch, skipped check, successful E2E run or commit.
- Obtain explicit approval for changes to normative requirements, public contracts, external provider permissions, security/privacy gates, persistence and runtime dependencies.
- `STATE.json` is the developer-controlled selection and acceptance checkpoint. Its optional `selectedTaskPath` is a context pointer, not an authorization or a check result. Do not change workstream phases or feature acceptances as a side effect of task decomposition.

## Flat task documents

- For each newly structured selected sub-spec, use `docs/specs/active/<scope>/` with a flat document set: `subspec.md`, `impl_plan.md`, and paired `task_<nn>_<slug>.md` / `task_impl_plan_<nn>_<slug>.md` files. No nested tasks/implementation-plans folders or second normative copies.
- Each numbered pair uses exactly the same numeric ID and slug; the stable task ID in its content survives file moves. Keep relative links, `STATE.json`, schemas, the feature cross-reference and the specification index consistent.
- `subspec.md` owns cross-task requirements, acceptance oracles and scope limits. `impl_plan.md` owns dependency order, existing public interfaces, task pointers and review gates, without repeating task-by-task code details.
- A task document defines one independently reviewable outcome, normative ID references, explicit non-goals, dependencies, single change partition, and observable positive/negative acceptance oracles. The paired implementation plan defines the exact read/change boundaries, existing versus proposed files, relevant `api.py` / `contract.md`, transport/error semantics and verification inventory.
- Only the selected workstream needs full task decomposition. An existing paused legacy workstream may retain its current `active/subspecs/` files until expressly selected; do not clone its normative requirements or silently change its approval state.

## Four source partitions and task handoff

- New concatenated snapshots are separately supplied as **frontend**, **backend**, **tests**, and **docs**. A selected task must identify exactly one **change partition** and may not modify files in any other partition, even when it reads contracts there. See [workflow](../DEVELOPMENT_WORKFLOW.md) for path classification and snapshot requirements.
- Require a compatible baseline identity, manifest and the complete ordered preceding PATCH overlays before writing changes. A missing required partition, file or patch is a blocker; do not infer contents from a different or older snapshot.
- Before editing, read the selected task and plan, applicable guidance, normative anchors, README and public API/contracts, plus the smallest affected source files. Do not read other task plans or archives by default. A cross-part public contract change is performed in its owning partition first, followed by a separate dependent task in the consumer partition.
- Each PATCH contains only source changes belonging to its one partition. Keep `apatch` reserved metadata separate from repository source. A task may use several PATCH repairs on its unfinished branch without broadening the partition.

## Sub-spec completion and verification policy

- Use **one feature branch for the entire selected sub-spec**, including all partition-scoped implementation tasks, end-of-sub-spec test preparation, repairs and final verification. Do not merge an individual task or open a new feature branch for each partition. Advance or accept the sub-spec only after its complete gate and developer review.
- **Do not run tests during ordinary implementation tasks.** This includes unit, contract, architecture, browser/UI E2E, Python HTTP E2E and database/integration suites, whether automatic or manual. Do not use `CHK` or a hidden test-runner substitute. Task acceptance oracles remain a review checklist, not claimed test evidence. Formatting is allowed but does not prove correctness.
- Preserve existing tests untouched throughout implementation; never rewrite, weaken, delete or add tests to manufacture a pass. Test editing belongs exclusively to the final `tests`-partition phase, after all implementation tasks for the sub-spec have been delivered.
- The final verification phase first creates or adjusts independent UI/Playwright, Python endpoint and integration E2E cases, then reviews existing unit/contract/architecture tests, removes only genuinely obsolete cases with a recorded rationale, and generates missing coverage. **Only after the test suite is ready** run all applicable unit, contract, architecture, backend endpoint, browser/UI E2E and integration tests plus canonical format/lint/type/build checks. Use a disposable PostGIS database for required DB integration; intercepted browser API calls do not prove real backend behavior. Report `PASS`, `FAIL`, `NOT RUN` or `BLOCKED` accurately, including external-source limitations.
- Any failure blocks completion: repair its owning partition in another scoped task/PATCH on the **same branch**, then repeat the affected checks and the full final gate on the final bytes. Never weaken an independent test merely to green a failed implementation. Runtime validation, security restrictions, source access and privacy constraints apply throughout, even when testing is deferred.
- Do not commit, push, create a PR or merge into `main` until **all required** tests and checks are actually successful and the developer authorizes publication. Unavailable required tests block merge rather than counting as a pass.

## `apatch` during the fast cycle

- Start the selected sub-spec once with `APL,BRN,FMT,STS` from a verified clean base; every later task and repair uses a **new ZIP on the same verified unfinished feature branch** with `APL,FMT,STS followup=true`. Do not create a new branch between tasks. `FMT` may mutate files (potentially across partitions), so inspect its result and stop on unrelated modifications; `CHK` is intentionally omitted throughout implementation and test-authoring tasks.
- The installed `apatch` requires valid `CHK` evidence for `CMT`. Do not add `CMT`, `PSH`, `PR`, `MRG` or `SYN` while checks are deferred. Uncommitted changes accumulate on the one feature branch; this is a limitation of the current tool, not proof of committed task milestones. Inspect `STS` before each follow-up; do not replay an already applied ZIP after any failure.
- Once the complete tests-partition phase has produced passing manual UI/E2E/integration evidence for the final bytes, run the real configured canonical `CHK` (including reviewed ordinary tests). Then, and only then, use guarded `CMT,PSH,PR,MRG,SYN,STS` after authorization. A change after the gate invalidates affected evidence and requires re-verification. Never overwrite ignored `.apatch/config.yaml`, weaken `run-tests.sh`, or alter external `apatch` safety to bypass this order.

## Traceability and history

- Keep `docs/FEATURES.md` as a feature catalog, not a task diary. Keep `feature-cross-ref.yaml` aligned with canonical sub-spec paths and actual verified owners/test paths; `implementation_status: verified` requires an accepted `STATE.json.featureAcceptances` record and human approval evidence.
- Keep plans and READMEs current-state; do not append generated-PATCH histories. Archive accepted workstreams only after developer approval, preserving normative IDs and updating canonical links. `archive/` is not normal task context.
- Do not edit other `AGENTS.md` files unless explicitly authorized. Never claim E2E coverage, external provider availability, source reuse rights, tests or Git publication without observed evidence.
