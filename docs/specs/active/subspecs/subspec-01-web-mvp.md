# MVP-01 Web — Browser Workflow Sub-specification

- **Status:** ACTIVE — W01 in implementation; acceptance pending
- **Requirements approval:** APPROVED — initial W01 user journey
- **Implementation authorization:** AUTHORIZED — selected Web workstream
- **Acceptance:** PENDING
- **Parent stage:** [`MVP-01`](../../umbrella_spec_melliatlas.md#mvp-01--working-sustainable-beekeeping-mvp)
- **Related active workstream:** [Backend sub-spec](subspec-01-backend-planning.md)
- **Implementation plan:** [MVP-01 Web plan](subspec-01-web-mvp_implementation_plan.md)
- **Selected next-task design (not yet implemented or accepted):** [Saved place and editable bbox](../tasks/web-saved-place-bbox/task.md). This design does not replace the currently approved W01 requirements or authorize new storage dependencies.

## 1. User journey and scope

A beekeeper opens **one responsive client**, selects a country, a supported territory, a season and an optional starting point, requests a **clearly marked synthetic** investigation, and compares planned stops, reported treatment windows, ecological cautions and alternative locations. Map selection and the seasonal timeline refer to the same stop and evidence. The user can revisit a completed investigation by its opaque ID while the backend still retains it.

Pesticide-treatment information is the primary practical focus; forage and ecology are evaluated alongside it. A source report, a geometric proximity result, a synthetic rule and a validated chemical-exposure model are distinct concepts. No UI treatment status may imply that spraying occurred, that wind-borne exposure was calculated, or that a candidate is safe.

This workstream does **not** port the former administration interface, map components or navigation from the historical repository. There is no separate Admin client, provider-configuration screen, login, automatic live collection or alerts. One read-only executable-scenario discovery operation supports the server-driven W01 controls; it is not source ingestion or a reference geography catalog. The only MVP UI is `web/`.

## 2. Requirements

| ID | Observable browser requirement | Umbrella anchor |
| --- | --- | --- |
| `MVP01-WEB-R01` | Provide one responsive React/TypeScript/Leaflet application with a keyboard-accessible map-adjacent workflow and no Admin surface. | `MVP-01.R01`, `R08` |
| `MVP01-WEB-R02` | Select an API-advertised country (currently RU/BY), display only API-backed regions and supported districts, select an imported district by map click when the point is unambiguous, and show unavailable/partial geometry explicitly. Do not invent administrative coverage or use provider-specific IDs as canonical IDs. | `MVP-01.R10`–`R14` |
| `MVP01-WEB-R03` | Let a user choose a season and optional WGS84 point, validate them locally, and submit them in a POST body only. Mark the available demonstration scenario as synthetic, without claiming live provider capability. | `MVP-01.R02`, `R08`, `R09` |
| `MVP01-WEB-R04` | Handle `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, domain outcomes without a plan, typed HTTP errors, polling cancellation and stale responses. Preserve the investigation ID for reopening without persisting private coordinates in a URL or browser storage. | `MVP-01.R07`–`R09` |
| `MVP01-WEB-R05` | Show ordered stops together on the map and seasonal timeline, with date windows, forage level and relocation count; explain why an original candidate was replaced and why alternatives remain provisional. | `MVP-01.R04`–`R08` |
| `MVP01-WEB-R06` | Show reported field-treatment dates, products, reported bee-hazard classes, geometric proximity and uncertainty separately from fictional ecology exclusions and cautions. Do not turn unreported/no-overlap into a safety verdict. | `MVP-01.R05`, `R08`; `SYS-02`, `SYS-04` |
| `MVP01-WEB-R07` | Present evidence IDs, source mode, synthetic marker, decision history and limitations in a legible details view. Never describe a fixture as a live Saturn or public-web observation. | `MVP-01.R05`, `R08`, `R13` |
| `MVP01-WEB-R09` | Provide RU and EN UI localization with one explicit language selector; extend translations through a typed resource dictionary, not country-dependent conditional rendering. | `MVP-01.R01`, `R08` |
| `MVP01-WEB-R10` | Discover executable synthetic scenarios and their country, territory and inclusive supported season from the backend. No scenario identifiers, fixture territory IDs or fixture years may be embedded in production browser code; empty country coverage is an explicit state. | `MVP-01.R02`, `R09` |
| `MVP01-WEB-R11` | When explicitly enabled, expose a manually triggered RU-only public Saturn notice preview through a bounded backend adapter, allowing explicit follow-up page reads without automatic crawling. Discover source availability by country, keep live reports separate from synthetic investigations, preserve provenance and uncertainty, and fail visibly on unavailable upstream data. Never imply complete coverage or reuse authorization. | `MVP-01.R05`, `R08`; `SYS-02`, `SYS-14` |
| `MVP01-WEB-R08` | Preserve predictable empty/loading/error states, mobile/touch usability, visible focus and basic screen-reader semantics; do not expose protected source contents or private apiary coordinates in logs, query strings or telemetry. | `MVP-01.R01`, `R09`; `SYS-14` |

## 3. UX composition

The default view is a **map-first workspace**, not a list of provider operations. A compact territory/season control region frames a map and synchronized horizontal timeline. Choosing a stop highlights its map position, time interval and explanation. A contextual evidence panel distinguishes (a) a source-reported planned treatment, (b) synthetic spatial screening, (c) ecology rules, and (d) unanswered questions such as wind and data coverage. On narrow screens these elements form a coherent vertical sequence; no hover-only action is essential.

Use restrained, distinct encodings for *reported notice*, *demonstration exclusion*, *caution*, *unknown* and *selected alternative*. Do not present a single red/green 'safe/unsafe' gradient. A source attribution is inspectable without requiring the user to understand ingestion internals. A map tile failure must not erase the accessible stop and evidence list.

The country selector is independent of source applicability. Country/region/district navigation and **validated real geography** must be distinguished from **synthetic planning evidence**. When a reference is unavailable (`503`), the UI displays a bounded explanation rather than fictional boundaries. A clearly labeled development demonstration can still be run through the existing fixture API when its parameters are explicitly selected.

## 4. Acceptance scenarios

| ID | Browser-observable oracle |
| --- | --- |
| `MVP01-WEB-A01` | Start an explicit synthetic RU investigation from the client; after completion show at least two ordered stops, relocation timing and both fictional treatment and ecology explanations. |
| `MVP01-WEB-A02` | Selecting a stop via either map or timeline updates the same selected stop and evidence panel; map-base-layer failure does not hide the accessible summary. |
| `MVP01-WEB-A03` | A restricted or treated candidate is not displayed as the final qualified choice, while its reasons remain inspectable; unknown coverage is not rendered as safe. |
| `MVP01-WEB-A04` | Loading, `FAILED`, no-plan, `404`, `409`, `422`, `503`, aborted request and stale-result cases show distinct, actionable states without fabricating an assessment. |
| `MVP01-WEB-A05` | Reload/reopen by investigation ID displays the same immutable completed response when the backend store is available; a lost in-memory result is shown as unavailable, not silently recomputed. |
| `MVP01-WEB-A06` | RU/BY switching and region navigation use verified catalogs when provided; unsupported districts or missing reference data are accurately communicated. |
| `MVP01-WEB-A07` | Browser checks cover touch viewport, keyboard navigation, focus handling, synthetic labeling, evidence attribution and absence of private point data in navigable URLs/logs. |
| `MVP01-WEB-A08` | EN/RU UI switching, third-country API fixture, server-provided season bounds, absence of scenarios, and cancellation after country changes are tested without a country-specific browser branch. |
| `MVP01-WEB-A09` | With live reading explicitly enabled, RU advertises Saturn and one manual page can display source-attributed notices or an explicit error; BY has no Saturn capability and causes no provider I/O, including for direct cross-country POST requests. An empty page is never treated as complete. |

## 5. Dependencies, gaps and explicit gates

- **Implemented API:** `GET /api/v1/territories/countries`, `/regions`, `/districts`, `/geometry/{territory_id}` and `POST/GET /api/v1/investigations`, plus read-only `GET /api/v1/investigations/scenarios?country=...` and the experimental, opt-in `GET /api/v1/sources` / `POST /api/v1/sources/saturn/treatments`. Contract details are owned by [`backend/src/melliatlas/api/contract.md`](../../../../backend/src/melliatlas/api/contract.md), the Python DTOs and OpenAPI, not this proposal.
- **Known gaps:** the experimental `GET /api/v1/sources` advertises explicitly enabled Saturn (RU only) and weather (when configured); it does not claim complete source coverage, paginated investigation history or verified complete RU/BY reference dataset. Executable synthetic scenario identifiers, territory associations and supported seasons are exposed by the new read-only discovery operation; it does not provide reference geography, permissions or real source coverage. Completed snapshots are durable only with an explicitly configured and independently verified PostGIS store.
- **Web authorization:** the W01 slice includes an explicitly enabled, bounded RU-only live notice preview alongside the fictional browser investigation. The preview remains opt-in and separate from investigation decisions. Backend acceptance and umbrella MVP-01 acceptance are still pending. Runtime credentials, live sources and third-party data reuse remain separately gated.
- **Environmental evidence:** no verified/current Saturn API contract, permission to reuse live Saturn data, validated pesticide drift or weather-based exposure model is delivered by MVP-01. No synthetic treatment result provides a permission or safety conclusion.

## Current W01 territory and source safeguards

The browser may persist only public geographic selection IDs and camera state.
Restoration requires server-confirmed country, region and district identity.
The selected territory's validated reference geometry authorizes one automatic
point weather preview on page load; there is no scheduled polling or automatic
Saturn collection. An explicit selected-area source read must be district-
scoped through an independently reviewed Saturn district ID, with a bounded
default source date interval of today through one calendar month. If a provider
mapping is absent, the read is unavailable rather than widened to the entire
region. Source filter accuracy and rights are not established by the demo.
The map and adjoining analysis panels occupy the available content width.


## Current W01 map and weather presentation (partial)

In the main live-source workspace, the beekeeper title and tagline belong in
the masthead, not the navigation sidebar. The map is modestly taller and has a
visible ephemeral starting-point explanation immediately above it. The weather
panel shows one UTC hour by default; remaining hours are in a keyboard-operable
disclosure, without suppressing model/provenance limitations. An empty Saturn
response is clearly labeled as no returned identified records, not a guarantee
of no spraying. Manually changing one date automatically keeps the other date
inside the one-calendar-year backend limit. Russian display labels for imported
Smolensk districts may come from optional reviewed `name_ru`; missing labels
fall back to the original imported name. A honey-orange, grey and charcoal
palette changes only presentation, not source semantics or readiness.

## Current Smolensk Saturn district mapping safeguards

The local administrator may explicitly capture one public Saturn directory
response for subject 55 and review a proposed Smolensk ADM2 district-to-source
identity mapping. Only a separately approved capture digest authorizes an
insert into the existing source-specific mapping table. Unmatched and ambiguous
districts remain unavailable, preserving the district-only scope requirement
and the 100-record manual page limit. Historical source examples do not
establish current provider operation, complete district coverage or permission
to collect; the workflow performs no implicit network request on startup.

