# Web — beekeeper workspace

`web/` is the **only** MelliAtlas browser client. It is a React 19 / TypeScript / Leaflet Vite application. There is no operator/Admin UI, no live pesticide-source collection and no browser telemetry.

The first W01 workspace lets a beekeeper select an API-advertised country and executable fictional scenario, choose a server-bounded season and optional private point, run the existing FastAPI investigation, and explore stop alternatives using a map, seasonal timeline and attributed ecology/treatment findings. Source claims and synthetic geometric screening are not confirmed spray events or safe-placement assessments. Country, scenario and region controls read the API; when validated RU/BY catalogs are missing, the app displays the HTTP `503` limitation instead of inventing regional coverage.

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
