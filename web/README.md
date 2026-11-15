# Web

This directory is reserved for the **single beekeeper-facing** React/TypeScript application. It is not runnable yet: there is no package manifest, installed UI dependencies, or configured build command. No separate Admin application is part of MVP-01.

## Proposed first vertical slice

The [proposed Web sub-spec](../docs/specs/proposals/subspec-01-web-mvp.md) and [implementation plan](../docs/specs/proposals/subspec-01-web-mvp_implementation_plan.md) describe a map-first study workspace: season and territory selection, an explicit synthetic investigation, a synchronized map/timeline, attributed treatment and ecology findings, alternative stops and visible uncertainty.

The current FastAPI backend supports investigation POST/GET and territory reads, but complete approved RU/BY references, source/scenario discovery and default durable results are not available. The client must display these gaps explicitly rather than substitute invented coverage. These proposal documents do not authorize Web implementation or approve new dependencies; see [specification status](../docs/specs/README.md).

`src/` is reserved for application code and `tests/` for browser checks. Document verified setup, usage and test commands in the corresponding `docs/` guides once a runnable client is implemented.
