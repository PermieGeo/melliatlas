# MelliAtlas

MelliAtlas is a geospatial decision-support application for **seasonal apiary placement and migratory beekeeping**. It helps beekeepers compare forage opportunities across territories and plan when to move an apiary during the flowering season. The application gives equal consideration to the conservation of wild pollinators and sensitive habitats.

The intended result is an **explainable seasonal placement plan**: candidate stops, proposed dates, reasons for selection or rejection, alternative locations, and the limits of the available evidence. MelliAtlas does not guarantee honey yield or certify that a location is ecologically safe.

## Purpose and users

MelliAtlas is designed around three related uses:

- **Beekeeping:** compare seasonal forage windows, identify gaps between flowering periods, and plan successive apiary stops with practical and ecological constraints.
- **Conservation:** identify protected or sensitive areas, distinguish binding restrictions from potential ecological concerns, and compare less disruptive placement options.
- **Research:** examine geographic and seasonal evidence about managed and wild pollinators. Later stages will support field observations, research datasets, and multi-year monitoring.

The first working product serves a beekeeper planning a seasonal relocation. Conservation checks are part of that workflow from the beginning; research tools are introduced incrementally.

## Conceptual model

```mermaid
flowchart LR
    B["Beekeeper<br/>Location and season"] --> M["MelliAtlas<br/>Evidence-based analysis"]
    F["Forage availability<br/>and flowering periods"] --> M
    E["Wild pollinators<br/>and ecological constraints"] --> M
    M --> P["Seasonal apiary plan<br/>Stops, dates and explanations"]
    M --> R["Conservation and research<br/>Evidence and uncertainty"]
```

The same territory may offer significant forage resources while also containing habitats where additional managed honey bees would be undesirable. MelliAtlas must evaluate these considerations together. A documented legal restriction, a possible ecological conflict, and a lack of information are **different findings** and must not be presented as interchangeable conclusions.

## Investigation request lifecycle

A beekeeper selects a **country, region, supported district, planning season, and point X**, and then requests an investigation. The diagram below is a **conceptual interaction diagram**. It shows how the request, background processing, cached source data, stored analysis results, weather updates, and repeated result checks fit together. It does **not** define the exact final persistence schema or the full set of HTTP endpoints.

```mermaid
sequenceDiagram
    autonumber
    actor Beekeeper
    participant Server as MelliAtlas server
    participant Sources as Source adapters
    participant Weather as Weather and forecast
    participant Cache as Cache / source database
    participant Engine as Analysis engine
    participant Results as Analysis results database

    Beekeeper->>Server: Request investigation for point X
    Server->>Server: Validate territory, season, and point
    Server->>Sources: Collect geographic, ecological, and public-source data
    Sources-->>Server: Raw source data
    Server->>Cache: Save source reads and metadata
    Server->>Weather: Fetch current weather and forecast
    Weather-->>Server: Weather update
    Server->>Engine: Normalize, process, and analyze evidence
    Engine->>Results: Save analysis result and decision trace
    Note over Server,Results: Data updates and forecast changes can trigger a refreshed analysis.

    loop Beekeeper checks the investigation status
        Beekeeper->>Server: Request investigation result
        alt Result not ready yet
            Server-->>Beekeeper: Investigation accepted or still running
        else Result available
            Server->>Results: Load latest saved result
            Results-->>Server: Availability verdict and nearby recommendations
            Server-->>Beekeeper: Point availability and recommended nearby points
        end
    end
```

The main interactions have the following meaning:

| Interaction | Expected behavior |
| --- | --- |
| **Beekeeper → Server: Request investigation for point X** | The request identifies the target location and planning context. The server validates the territory, season, and supported scenario before starting work. |
| **Server → Sources / Weather** | The backend gathers evidence from approved sources, including geographic and ecological inputs, public-web evidence, and weather or forecast information when that input is available for the stage. |
| **Server → Cache** | Source reads and their metadata are preserved in a cache or source-oriented store so that repeated processing can reuse retrieved evidence and keep provenance. |
| **Server → Engine → Results** | The analysis engine normalizes evidence, runs screening and comparison logic, and stores the resulting assessment, decision trace, and recommended alternatives in persistent storage. |
| **Refreshed analysis** | When source content changes or a newer weather forecast affects the interpretation, the backend may recompute the assessment and replace or version the stored result. |
| **Beekeeper polls for the result** | The beekeeper may ask for the result repeatedly. The response is either that the result is not ready yet, or the latest available assessment is returned. |
| **Returned assessment** | A completed response reports whether the requested point appears available in light of critical factors and, when appropriate, returns recommended nearby points. |

The diagram describes the **request-and-result interaction flow**, not the complete internal job model. Backend execution states, durable worker recovery, and provider-specific retry policies remain defined by the active backend specification and later implementation stages.

## Evidence and analysis

MelliAtlas is intended to combine geographic, temporal, agricultural, and ecological information. Potential sources include administrative boundaries and maps; vegetation and flowering calendars; public websites and news in Russia and Belarus; Russia-only FGIS Saturn evidence; weather information; protected-area restrictions; field observations of wild pollinators; and privately supplied apiary or travel constraints.

Potential processing components include geographic normalization, source provenance checks, forage-window analysis, spatial screening, comparison of candidate stops, uncertainty assessment, and seasonal plan construction. Sources provide data; analyzers process it; the engine executes typed dependent operations; and the agent determines whether further checks or revised candidates are necessary. These components are planned capabilities, not claims that the integrations already exist.

In **`MVP-01`**, Russia and Belarus require reference maps and regional catalogs, with district catalogs for Smolensk and Vitebsk Oblasts. Planning evidence, public-website/news samples, and Saturn examples remain **synthetic or fixture-based**. Real public-web/news ingestion for both countries and verified Saturn integration for Russia are scheduled for **`MVP-02`**, subject to source-access, licensing, and data-meaning checks.

Every significant conclusion should retain its source, relevant dates and geographic scope, the transformation or rule applied, and uncertainty. Synthetic material must be labeled as synthetic. The absence of evidence about pesticide treatments, wild pollinators, or nearby apiaries is not evidence that the area is safe.

## Development roadmap and current status

The product is developed in independently testable increments. **`MVP-01` must deliver an end-to-end browser workflow**, including a React/Leaflet map, a Python/FastAPI backend, a minimal deterministic agent, synthetic placement analysis with ecological screening, and reopening a completed result from PostgreSQL/PostGIS. Later stages add real data adapters, richer seasonality, stronger conservation and relocation analysis, optional LLM planning, research tools, and long-term ecological monitoring.

**Current status:** the implemented backend provides a FastAPI application factory, a health endpoint, OpenAPI metadata, and initial tests. Typed territory contracts, an offline reference validator, and versioned territory reads are now implemented, but no complete approved RU/BY catalog or real geometry dataset is loaded. PostGIS persistence, source adapters, the planning engine, agent behavior, and the React user interface are not yet implemented. Both diagrams describe the intended product behavior.

## Architecture and project documentation

The planned application is a **Python modular monolith** with FastAPI, PostgreSQL/PostGIS, and a single responsive React/TypeScript web client. An independent Python worker is introduced when durable background execution becomes necessary. LLM-based planning is optional; the initial agent must work without an LLM.

| Directory | Responsibility |
| --- | --- |
| `backend/` | API, domain contracts, sources, analyzers, execution, and persistence |
| `web/` | Map, seasonal plan, evidence presentation, and future research views |
| `config/countries/` | Country-specific configuration |
| `docs/specs/` | Umbrella specification, active sub-specifications, plans, and checkpoints |

The [umbrella specification](docs/specs/umbrella_spec_melliatlas.md) defines the roadmap and acceptance criteria. The [specification index](docs/specs/README.md) identifies the active workstream and the documents governing implementation. See [installation](docs/INSTALLATION.md) and [testing](docs/TESTS.md) for the currently supported commands.

