# MVP-01 Web — Proposed Browser Workflow Sub-specification

- **Status:** PROPOSED — requirements not yet approved
- **Implementation authorization:** NOT GRANTED by this proposal
- **Acceptance:** PENDING
- **Parent stage:** [`MVP-01`](../umbrella_spec_melliatlas.md#mvp-01--working-sustainable-beekeeping-mvp)
- **Related active workstream:** [Backend sub-spec](../active/subspecs/subspec-01-backend-planning.md)
- **Proposed implementation plan:** [MVP-01 Web plan](subspec-01-web-mvp_implementation_plan.md)

## 1. User journey and scope

A beekeeper opens **one responsive client**, selects a country, a supported territory, a season and an optional starting point, requests a **clearly marked synthetic** investigation, and compares planned stops, reported treatment windows, ecological cautions and alternative locations. Map selection and the seasonal timeline refer to the same stop and evidence. The user can revisit a completed investigation by its opaque ID while the backend still retains it.

Pesticide-treatment information is the primary practical focus; forage and ecology are evaluated alongside it. A source report, a geometric proximity result, a synthetic rule and a validated chemical-exposure model are distinct concepts. No UI treatment status may imply that spraying occurred, that wind-borne exposure was calculated, or that a candidate is safe.

This workstream does **not** port the former administration interface, map components or navigation from the historical repository. There is no separate Admin client, provider-configuration screen, login, live source collection, alerts or new public API in this sub-spec. The only MVP UI is `web/`.

## 2. Proposed requirements

| ID | Observable browser requirement | Umbrella anchor |
| --- | --- | --- |
| `MVP01-WEB-R01` | Provide one responsive React/TypeScript/Leaflet application with a keyboard-accessible map-adjacent workflow and no Admin surface. | `MVP-01.R01`, `R08` |
| `MVP01-WEB-R02` | Select RU or BY, display only API-backed regions and supported districts, and show unavailable/partial geometry explicitly. Do not invent administrative coverage or use provider-specific IDs as canonical IDs. | `MVP-01.R10`–`R14` |
| `MVP01-WEB-R03` | Let a user choose a season and optional WGS84 point, validate them locally, and submit them in a POST body only. Mark the available demonstration scenario as synthetic, without claiming live provider capability. | `MVP-01.R02`, `R08`, `R09` |
| `MVP01-WEB-R04` | Handle `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, domain outcomes without a plan, typed HTTP errors, polling cancellation and stale responses. Preserve the investigation ID for reopening without persisting private coordinates in a URL or browser storage. | `MVP-01.R07`–`R09` |
| `MVP01-WEB-R05` | Show ordered stops together on the map and seasonal timeline, with date windows, forage level and relocation count; explain why an original candidate was replaced and why alternatives remain provisional. | `MVP-01.R04`–`R08` |
| `MVP01-WEB-R06` | Show reported field-treatment dates, products, reported bee-hazard classes, geometric proximity and uncertainty separately from fictional ecology exclusions and cautions. Do not turn unreported/no-overlap into a safety verdict. | `MVP-01.R05`, `R08`; `SYS-02`, `SYS-04` |
| `MVP01-WEB-R07` | Present evidence IDs, source mode, synthetic marker, decision history and limitations in a legible details view. Never describe a fixture as a live Saturn or public-web observation. | `MVP-01.R05`, `R08`, `R13` |
| `MVP01-WEB-R08` | Preserve predictable empty/loading/error states, mobile/touch usability, visible focus and basic screen-reader semantics; do not expose protected source contents or private apiary coordinates in logs, query strings or telemetry. | `MVP-01.R01`, `R09`; `SYS-14` |

## 3. Provisional UX composition

The default view is a **map-first workspace**, not a list of provider operations. A compact territory/season control region frames a map and synchronized horizontal timeline. Choosing a stop highlights its map position, time interval and explanation. A contextual evidence panel distinguishes (a) a source-reported planned treatment, (b) synthetic spatial screening, (c) ecology rules, and (d) unanswered questions such as wind and data coverage. On narrow screens these elements form a coherent vertical sequence; no hover-only action is essential.

Use restrained, distinct encodings for *reported notice*, *demonstration exclusion*, *caution*, *unknown* and *selected alternative*. Do not present a single red/green 'safe/unsafe' gradient. A source attribution is inspectable without requiring the user to understand ingestion internals. A map tile failure must not erase the accessible stop and evidence list.

The country selector is independent of source applicability. Country/region/district navigation and **validated real geography** must be distinguished from **synthetic planning evidence**. When a reference is unavailable (`503`), the UI displays a bounded explanation rather than fictional boundaries. A clearly labeled development demonstration can still be run through the existing fixture API when its parameters are explicitly selected.

## 4. Proposed acceptance scenarios

| ID | Browser-observable oracle |
| --- | --- |
| `MVP01-WEB-A01` | Start an explicit synthetic RU investigation from the client; after completion show at least two ordered stops, relocation timing and both fictional treatment and ecology explanations. |
| `MVP01-WEB-A02` | Selecting a stop via either map or timeline updates the same selected stop and evidence panel; map-base-layer failure does not hide the accessible summary. |
| `MVP01-WEB-A03` | A restricted or treated candidate is not displayed as the final qualified choice, while its reasons remain inspectable; unknown coverage is not rendered as safe. |
| `MVP01-WEB-A04` | Loading, `FAILED`, no-plan, `404`, `409`, `422`, `503`, aborted request and stale-result cases show distinct, actionable states without fabricating an assessment. |
| `MVP01-WEB-A05` | Reload/reopen by investigation ID displays the same immutable completed response when the backend store is available; a lost in-memory result is shown as unavailable, not silently recomputed. |
| `MVP01-WEB-A06` | RU/BY switching and region navigation use verified catalogs when provided; unsupported districts or missing reference data are accurately communicated. |
| `MVP01-WEB-A07` | Browser checks cover touch viewport, keyboard navigation, focus handling, synthetic labeling, evidence attribution and absence of private point data in navigable URLs/logs. |

## 5. Dependencies, gaps and explicit gates

- **Implemented API:** `GET /api/v1/territories/countries`, `/regions`, `/districts`, `/geometry/{territory_id}` and `POST/GET /api/v1/investigations`. Contract details are owned by [`backend/src/melliatlas/api/contract.md`](../../../backend/src/melliatlas/api/contract.md), the Python DTOs and OpenAPI, not this proposal.
- **Known gaps:** there is no `GET /api/v1/scenarios`, `GET /api/v1/sources`, paginated investigation history or verified complete RU/BY reference dataset. Only documented fixture IDs may be offered as development options until a discovery API exists. Completed snapshots are durable only with an explicitly configured and independently verified PostGIS store.
- **Web authorization:** this is a proposed specification. Before implementing the Web workstream, review/approve its normative scope, record a deliberate workstream checkpoint, and approve any new runtime dependencies. Do not mark backend or umbrella acceptance complete as part of this handoff.
- **Environmental evidence:** no approved live Saturn/web ingestion, validated pesticide drift or weather-based exposure model is delivered by MVP-01. No synthetic treatment result provides a permission or safety conclusion.
