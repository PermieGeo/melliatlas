# Web — beekeeper workspace

`web/` is the single React 19 / TypeScript / Leaflet Vite browser client. Its current map-first workspace combines public territory navigation, a manually requested RU-only Saturn preview, an opt-in point weather preview, and a separate synthetic investigation demonstration. There is no Admin application, general live ingestion pipeline, background provider collection or production authentication.

## Run locally

Install Node.js 22+ and npm and set up the backend according to [installation instructions](../docs/INSTALLATION.md). Start the backend from the repository root:

```sh
python -m uvicorn melliatlas.main:app --host 127.0.0.1 --port 8000
```

Start the Web development server in another terminal:

```sh
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to `http://127.0.0.1:8000`. The repository snapshot does not include an npm lockfile; commit an actual resolved lockfile before claiming reproducible frontend installation.

**Network and privacy:** OpenStreetMap remote tiles are disabled by default. The user may explicitly enable an online basemap for the current map session; enabling it shares the viewed map area with the tile provider. Turning it off removes the tile layer. A complete offline basemap is not yet available. Private investigation `starting_point` and unsaved analysis-area coordinates are sent only in POST bodies and are not kept in browser localStorage, URL parameters or telemetry. Public territory IDs and the general map camera may be stored as separate local preferences. Explicitly saved private places are a proposed future feature, not current behavior.

## Current behavior and limitations

- **Country, region and geometry:** RU/BY countries and region names are provided by the API. Validated imported ADM1/ADM2 boundaries are optional. Missing or partial reference geography must be shown honestly; source-specific Saturn IDs are never synthesized from canonical territory IDs. Country/region changes cancel stale browser requests. The region selection and map can work without a fictional investigation.
- **Synthetic investigation:** requires `MELLIATLAS_SOURCE_PROVIDER=synthetic`. Server-advertised executable fixtures define the available dates, IDs and supported territory. The client starts/polls/reopens an investigation and displays stops, a timeline, treatment claims, ecology findings and limitations. Fictional decisions are not evidence of actual pesticide exposure.
- **Saturn preview (RU only):** enabled only by `MELLIATLAS_SATURN_LIVE_ENABLED=true`; the selected canonical district requires an independently reviewed source mapping. Manual page reads use the configured dates, up to **one calendar year**, with a maximum of **100 source records across 10 pages**. Missing mappings fail without regional fallback. A zero-record/partial read does not prove no treatments or complete coverage; source permissions and upstream date-filter semantics remain unverified.
- **Weather:** enabled only by `MELLIATLAS_WEATHER_LIVE_ENABLED=true` with database-configured Open-Meteo settings and a valid point. The current API provides **24 sequential UTC hours**. It does not provide a 15-day horizon, verified weather at the actual apiary, or pesticide drift assessment. The UI displays source attribution and uncertainty.
- **Unsaved area draft:** after choosing a region, the user can enable a temporary map-click draft, resize its 15 × 15 km rectangle (maximum 30 km per dimension), and explicitly request the imported ADM2 districts intersecting the area. The user may also enter independent latitude/longitude fields (decimal dot or comma). That action verifies the selected region through the existing body-only point resolver before moving the draft and focusing the map without changing zoom. The local outline is provisional, and the server distinguishes missing or unverified geographic coverage. No place is saved or identified as safe.
- **Persistence and future UI:** a disconnected owner-scoped backend storage adapter exists, but saved-place HTTP access, durable user place workflows, multi-layer regional data, coordinate/settlement search and offline storage are **not enabled**. The [selected design task](../docs/specs/active/tasks/web-saved-place-bbox/task.md) describes their first bounded slice without claiming implementation approval.

## Architecture

`src/api/{client,types,validation}.ts` and its [public contract](src/api/contract.md) own network input/output validation. `App.tsx` composes current workflows; `hooks/useInvestigation.ts` owns investigation request state, while `hooks/useAreaDraft.ts` owns the temporary place draft, cancellation and result invalidation. `components/MapPanel.tsx`, `ReferenceControls.tsx`, `LiveAreaAnalysis.tsx`, `WeatherPanel.tsx` and `Timeline.tsx` present the current geography, source and synthetic results. `i18n.ts` supplies RU/EN UI strings. No browser module imports Python implementation or provider-internal code.

The [approved Web sub-spec](../docs/specs/active/subspecs/subspec-01-web-mvp.md) owns current W01 requirements, and the [current integration plan](../docs/specs/active/subspecs/subspec-01-web-mvp_implementation_plan.md) owns task navigation. Neither implementation nor passing tests constitutes feature acceptance.

## Checks

```sh
cd web
npm run format:check
npm run lint
npm run typecheck
npm run test:ci
npm run build
npx playwright install chromium
npm run test:e2e
```

The browser E2E suite needs installed Chromium and Node dependencies. Unit/component tests use mocked HTTP and a backend-derived synthetic fixture; they do not prove live PostGIS or external provider compatibility. Run the repository-level `sh ./run-tests.sh` for canonical checks.
