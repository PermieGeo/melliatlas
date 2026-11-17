# Web — beekeeper workspace

`web/` is the **only** MelliAtlas browser client. It is a React 19 / TypeScript / Leaflet Vite application. There is no operator/Admin UI, no background source collection and no browser telemetry. Opt-in live Saturn reads and automatic, territory-selected weather previews are available in the current experimental UI.

The W01 workspace now starts with country-scoped live source access, independent of the fictional investigation. Where enabled, Saturn requires a reviewed district mapping and Open-Meteo receives a validated point inside the selected territory. An optional fictional scenario permits a separate FastAPI investigation with a bounded season, timeline and attributed ecology/treatment findings. Source claims and synthetic geometric screening are not confirmed spray events or safe-placement assessments. Country, scenario and region controls read the API; when validated RU/BY catalogs are missing, the app displays the HTTP `503` limitation instead of inventing regional coverage.

## Run locally

Install Node.js 22+ and npm. From the repository root, install backend dependencies as described in [`docs/INSTALLATION.md`](../docs/INSTALLATION.md). For the local HTTP server, install an approved ASGI runner such as `uvicorn` in the Python virtual environment.

In terminal 1:

```bash
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000
```

In terminal 2:

```bash
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies only `/api` to `http://127.0.0.1:8000`; browser calls are same-origin in development. The first installation creates `web/package-lock.json`; commit the generated lockfile before declaring a reproducible dependency setup. No package lockfile is fabricated without a successful dependency resolution.

The map starts with **remote tiles disabled**. Enabling the optional OpenStreetMap basemap sends map viewport/tile requests to an external service. The private starting point is sent only in the POST request body, never in URL parameters or browser storage. The initial demonstration uses invented site coordinates shown against a geographic viewport only for interaction testing.

## Checks

```bash
cd web
npm run format:check
npm run lint
npm run typecheck
npm run test:ci
npm run build
npx playwright install chromium
npm run test:e2e
```

Frontend unit tests and browser checks are offline API-mocked. The backend fixture in `tests/fixtures/combined.json` was produced from the actual FastAPI synthetic combined scenario and has stable test-only IDs/timestamps. Component tests mock only the Leaflet rendering boundary, not the typed HTTP client. Playwright requires an installed browser binary and Vite dependencies; its tests are separate from routine canonical checks.

## Architecture and current limits

- [`src/api/types.ts`](src/api/types.ts), [`src/api/validation.ts`](src/api/validation.ts), [`src/api/client.ts`](src/api/client.ts) are the only HTTP boundary; see the [API contract](src/api/contract.md).
- `App.tsx` composes API-advertised selections and views. `hooks/useInvestigation.ts` owns bounded polling, request cancellation and stale-response guards; `components/InvestigationControls.tsx` renders typed selections. `notifications.ts` maps errors without language-specific inline text, and `i18n.ts` provides RU/EN UI dictionaries. Map, timeline and evidence panels are presentational.
- W01 has no real boundary dataset, live source ingestion, wind-drift modeling, durable default server jobs, notifications or production authentication. A selection on the map is a demo starting point, not a validated apiary address.
- The [selected Web sub-spec](../docs/specs/active/subspecs/subspec-01-web-mvp.md) and [implementation plan](../docs/specs/active/subspecs/subspec-01-web-mvp_implementation_plan.md) define remaining W01 acceptance and follow-on work. A successful build alone does not approve the product feature.


### Country, language and synthetic scenarios

The country preference is the last validated public country ID, then RU when offered, otherwise the first returned country. Country names are rendered using the selected locale and `Intl.DisplayNames`; selecting any future backend-supported country does not require browser-side `if (code === ...)` branches. RU and EN labels are available independently of the chosen country. The English source-report/evidence wording is preserved as received and is not presented as a translated provider claim.

The client calls `GET /api/v1/investigations/scenarios?country=...` to list only executable fictional scenarios and their supported territory and season range. No synthetic territory IDs, scenario IDs or fixed fixture dates are compiled into the UI. A country without executable scenarios disables submission but still permits reopening a previously completed investigation. Validated region reference coverage remains a separate concern; a fictional scenario does not prove real boundaries.


The backend must be started with `MELLIATLAS_SOURCE_PROVIDER=synthetic` for the
fictional W01 investigation demo. Without this explicit choice, scenario discovery
returns no executable entries and the workspace shows its unavailable state.

## W01 reference navigation (partial R02)

The reference region/district navigation is independent of synthetic scenario selection. It uses the existing territory catalog and WGS84 geometry API. Once a validated reference dataset is explicitly loaded on the backend, selecting a region displays its published geometry and only supported district options; selecting a district displays its own boundary. HTTP `409` means district depth is unsupported; `404` means geometry is missing; `503` means the catalog is unavailable. Older country/territory requests are cancelled and cannot draw a stale boundary. The map displays the reference ID and never invents boundaries when no references are installed. This does not establish full RU/BY inventory approval or W02 acceptance.

## Experimental public Saturn preview (RU only)

When `MELLIATLAS_SATURN_LIVE_ENABLED=true`, users may request one page of
unverified Saturn notices for the currently selected canonical RU district.
Each district ID must have a separately operator-reviewed Saturn provider code
stored in `melliatlas_source_saturn_district` after migration `0005`; no region
fallback is allowed. A manual date interval defaults to local today through
one calendar month, with a server-enforced maximum of 31 days. This maps to
candidate upstream `UpdateMap` date filters, not verified spraying dates.
Missing mappings return 409, and no network request occurs. Source completeness,
filter compatibility and access/reuse permission remain unverified; no
background crawling or safety conclusion is provided.

## Live on-demand weather preview

With `MELLIATLAS_WEATHER_LIVE_ENABLED=true`, the browser automatically reads
one 24-hour Open-Meteo forecast whenever a validated territory and a point
inside its approved polygon are available. Forecast wind, gusts, direction
and precipitation are displayed in an inline panel above the map (without a
new browser window). A click inside the selected boundary can change the
forecast point, which is never stored. There is no scheduled polling or
pesticide-drift assessment. The free endpoint requires appropriate attribution
and non-commercial use.

## Live-first navigation when no reference catalog is loaded

Country and public source discovery are independent of fictional investigation
metadata. A local server with no imported ADM1/ADM2 geometry offers country and
region-name navigation but cannot construct a verified district selection or
an automatic representative weather location. Configure reviewed PostGIS
boundaries and the explicit live-weather gate to enable the geographic
forecast; configure reviewed Saturn district mappings and its gate for a
manual district read. No source identifiers or boundaries are inferred.

## Area-first beekeeper workflow (W01 partial)

Select a country, region and reviewed district. Public country/region/district
IDs are stored in browser `localStorage` (`melliatlas.territory.selection.v1`)
and restored only after each API catalog validates them. The independent map
camera uses `melliatlas.map.viewport.v1`. Point coordinates are never persisted.
A valid WGS84 polygon is required before the map fits the selected territory,
chooses a representative point inside it and automatically loads the 24-hour
weather preview above the map. The map and timeline/evidence panels extend to
the right edge, with navigation controls in a left sidebar.

The **Analyze selected area** action is available only for a reviewed district
with a validated boundary and a date range of at most 31 days. The backend
resolves its Saturn provider district code from an independently reviewed
mapping; an unmapped district never silently triggers a region-wide read. The
date filter defaults to today through one calendar month. All findings remain
partial source claims, not confirmation of spraying, coverage or site safety.


## Compact live-data workspace (W01 follow-up)

The top header displays the beekeeper-oriented product title and tagline. The
left sidebar keeps only geographic selection, Saturn date controls, and an
explicitly enabled fictional-demo disclosure. The optional starting point is
explained in a contrasting panel directly above the taller map. Open-Meteo
renders its first UTC forecast hour immediately, with the other hours inside
an accessible native details disclosure. Saturn zero-record responses receive
an explicit partial/unknown-coverage message, never a statement of safety.
The honey-orange/charcoal palette uses CSS styles, not map model constants.
Manual Saturn dates auto-adjust their opposite bound if a change would exceed
the backend's 31-day request limit. A limited Smolensk ADM2 localization uses
an optional server-provided `name_ru` while English still uses the unchanged
source `name`; apply migration `0006` before the localized DB-backed API runs.

### Investigation lifecycle enums

The wire-level investigation statuses and outcomes come from the Python backend
enums. `src/api/generated/investigationEnums.ts` is generated, not manually
maintained. See the backend README for the regeneration command.
