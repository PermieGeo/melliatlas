# Web — beekeeper workspace

`web/` is the **only** MelliAtlas browser client. It is a React 19 / TypeScript / Leaflet Vite application. There is no operator/Admin UI, no background source collection and no browser telemetry. Opt-in, manual-only live Saturn and weather reads are available in the current experimental UI.

The W01 workspace now starts with country-scoped live source access, independent of the fictional investigation. Where enabled, Saturn accepts a manually verified upstream subject code and Open-Meteo accepts a point chosen on the map. An optional fictional scenario permits a separate FastAPI investigation with a bounded season, timeline and attributed ecology/treatment findings. Source claims and synthetic geometric screening are not confirmed spray events or safe-placement assessments. Country, scenario and region controls read the API; when validated RU/BY catalogs are missing, the app displays the HTTP `503` limitation instead of inventing regional coverage.

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

The country preference is RU when the API advertises it, otherwise the first returned country. Country names are rendered using the selected locale and `Intl.DisplayNames`; selecting any future backend-supported country does not require browser-side `if (code === ...)` branches. RU and EN labels are available independently of the chosen country. The English source-report/evidence wording is preserved as received and is not presented as a translated provider claim.

The client calls `GET /api/v1/investigations/scenarios?country=...` to list only executable fictional scenarios and their supported territory and season range. No synthetic territory IDs, scenario IDs or fixed fixture dates are compiled into the UI. A country without executable scenarios disables submission but still permits reopening a previously completed investigation. Validated region reference coverage remains a separate concern; a fictional scenario does not prove real boundaries.


The backend must be started with `MELLIATLAS_SOURCE_PROVIDER=synthetic` for the
fictional W01 investigation demo. Without this explicit choice, scenario discovery
returns no executable entries and the workspace shows its unavailable state.

## W01 reference navigation (partial R02)

The reference region/district navigation is independent of synthetic scenario selection. It uses the existing territory catalog and WGS84 geometry API. Once a validated reference dataset is explicitly loaded on the backend, selecting a region displays its published geometry and only supported district options; selecting a district displays its own boundary. HTTP `409` means district depth is unsupported; `404` means geometry is missing; `503` means the catalog is unavailable. Older country/territory requests are cancelled and cannot draw a stale boundary. The map displays the reference ID and never invents boundaries when no references are installed. This does not establish full RU/BY inventory approval or W02 acceptance.

## Experimental public Saturn preview (RU only)

When the backend explicitly sets `MELLIATLAS_SATURN_LIVE_ENABLED=true`, the
client discovers the public Saturn source for RU and offers a manual one-page
read by the upstream numeric subject code. The same UI does not expose Saturn
for BY or other countries. Returned unverified notices and available source
polygons appear independently of the offline synthetic investigation. Empty or
failed requests prove neither absence of spraying nor complete source coverage;
there is no current-date filtering or automatic crawling. Provider compatibility
and reuse terms require independent validation before public deployment.

## Live on-demand weather preview

With `MELLIATLAS_WEATHER_LIVE_ENABLED=true` on the backend, select any map point
and click **Read 24-hour forecast**. Weather displays forecast 10-m wind,
reported direction, gusts and precipitation separately from Saturn notices and
fictional investigation results. This forwards the selected point to
Open-Meteo via the server; no automatic polling, browser persistence or drift
safety judgment occurs. A disabled/unreachable source is not assumed to have
zero wind. Displayed data are attributed to Open-Meteo (CC BY 4.0); the free
endpoint is licensed for non-commercial use only.

## Live-first navigation when no reference catalog is loaded

The country selector and on-demand live-source panels do **not** require fictional
investigation metadata. With the default `MELLIATLAS_SOURCE_PROVIDER=disabled`,
the fictional territory, scenario and season controls are not rendered; an
explicit status explains the unavailable demo and links to the live sources.
A missing validated region catalog still produces `503` and leaves geographic
region selection unavailable. This must not be replaced with fabricated
administrative regions or assumed Saturn subject-code mappings.

For a local live preview, explicitly enable the opt-in Saturn and weather
adapters in the backend as documented above. The Saturn panel accepts only a
manually verified upstream subject code; weather reads require a point selected
on the map. For BY, Saturn is never offered, but weather can be available.


### Preseeded country region navigation

With the optional PostgreSQL region directory configured on the backend, the
left panel offers independent RU/BY ISO-coded first-order regions. Saturn uses
the selected canonical region ID and a server-owned mapping table; no manual
numeric Saturn code is entered. Regions with no verified Saturn mapping return
`409/SOURCE_REGION_UNMAPPED` without contacting the provider. The initial seed
contains only the archived Smolensk source mapping. Region borders and pilot
districts are not included in the name-only seed; their absence is explicit.
