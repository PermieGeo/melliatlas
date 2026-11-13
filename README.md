# MelliAtlas

**Better decisions for migratory beekeeping, wild pollinators, and the ecosystems they share.**

MelliAtlas is a geospatial decision-support application for planning where and when to place or move apiaries during the flowering season. It is designed to help beekeepers follow changing nectar and pollen resources while accounting for the wellbeing of their colonies, practical relocation constraints, and the needs of wild pollinators.

The goal is **not to maximize honey collection at any cost**. Productive apiary locations can overlap with protected habitats, compete for limited floral resources, or be unsuitable for other reasons. MelliAtlas aims to make these trade-offs visible and help people find responsible alternatives.

## Who it is for

- **Beekeepers:** compare prospective apiary stops, explore flowering periods, spot gaps in the honey-flow season, and build an explainable relocation plan.
- **Conservation practitioners:** inspect protected areas, sensitive habitats, and potential conflicts between managed and wild pollinators; compare alternative site arrangements.
- **Ecologists and researchers:** examine spatial and seasonal evidence, compare hypotheses and territories, and eventually record field observations and monitor ecological changes over multiple years.

The initial product experience is for beekeepers. Research and conservation capabilities grow on the same geospatial and analytical foundation rather than as separate applications.

## How it should work

A beekeeper selects an area and season, provides a starting location, and asks MelliAtlas to explore possible apiary stops. The application evaluates available evidence about flowering resources, geography, environmental constraints, and other relevant conditions. It presents candidate stops and a **tentative, sequential seasonal plan** on a map and timeline, with explanations and alternatives.

An analysis agent may request additional data or revise its proposed course of action when evidence is missing or contradictory. The agent does not replace scientific validation or independently grant permission to use a site.

For a conservation or research task, the same foundation can be used to compare areas, examine possible ecological pressures, and trace conclusions back to observations and methods.

## Principles

1. **Useful from the first release.** The first implementation stage delivers a small but complete browser-to-backend experience, including a map, an apiary relocation plan, and a meaningful ecological constraint. Each later stage improves this working application.
2. **Beekeeping and biodiversity both matter.** An attractive honey-flow prospect must not automatically outrank a verified restriction or an important ecological concern.
3. **Evidence, not invented certainty.** Distinguish actual observations, estimates, model outputs, missing data, and synthetic demonstrations. Never turn an absence of evidence into a claim of safety.
4. **Legal restrictions are not scientific estimates.** Present confirmed rules separately from possible ecological impacts; do not invent universal exclusion distances or legal prohibitions.
5. **Explain decisions.** Show the data sources, analytical steps, uncertainty, and reasons for choosing, rejecting, or reconsidering a site.
6. **Protect sensitive locations.** Exact private apiary coordinates and sensitive species observations require appropriate access controls before any multi-user or public use.
7. **Prefer an extensible, comprehensible system.** Add data sources, analyzers, and research workflows incrementally through explicit contracts, without turning MelliAtlas into a general-purpose GIS framework.

## Initial implementation

The first release will use **clearly labeled synthetic data** to demonstrate a seasonal plan with multiple candidate stops. It will include a case where a promising location is rejected because of a **synthetic, explicitly defined exclusion rule**, and the analysis produces an alternative. This is a software demonstration, not advice about real land, real conservation restrictions, or predicted honey yields.

Later stages add more realistic flowering models, adaptive analysis, persistence and background processing, verified real datasets, geography across territories, ecological assessments, planning constraints, research comparisons, and field monitoring.

## Repository overview

| Path | Responsibility |
| --- | --- |
| `backend/` | Python/FastAPI application, typed analysis engine, agent, sources, analyzers, persistence, and worker capabilities |
| `web/` | React/TypeScript application with maps, planning views, reports, and later research workflows |
| `config/countries/` | Country-specific source and analysis configuration as the product expands |
| `docs/specs/` | Product specification, selected sub-specifications, implementation plans, and SDD state |
| `docs/FEATURES.md` | Stable feature identifiers and short descriptions |

The target architecture is a Python modular monolith with PostgreSQL/PostGIS and a separate worker when durable processing is introduced. The browser client uses React, TypeScript, Vite, Tailwind CSS, and Leaflet. Sources and analyzers provide typed capabilities to an execution engine; a bounded agent can select and revise analysis operations. An LLM is optional and is not a prerequisite for the first MVP.

**This repository is currently a scaffold.** The architecture and features described here are intended behavior, not a claim that the API, database, client, or analytical models are already implemented.

## Specifications and delivery

The [umbrella specification](docs/specs/umbrella.md) defines the product's requirements, scope, ordered stages, and acceptance outcomes. Its first stage, **MVP-01**, delivers the initial end-to-end application. Sub-specifications and their separate implementation plans are prepared **only when a stage is selected**; implementation follows those approved requirements.

The [specification index](docs/specs/README.md) records the current documentation lifecycle. Engineering instructions live in the relevant `AGENTS.md` files; this README describes the product and repository for human readers.
