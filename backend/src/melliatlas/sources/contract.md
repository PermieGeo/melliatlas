# Source Provider Contract

The public capability boundary is `melliatlas.sources.api`: `ScenarioProvider` is a
structural Python `Protocol`, and `ScenarioListing` advertises the identity, country,
territory, source mode, inclusive supported season and default status of an executable
scenario. `ScenarioProvider.load(country=..., territory_id=..., scenario_id=...)`
returns a typed scenario or `None` for an unsupported combination;
`list_scenarios(country)` returns only scenarios the provider can actually load.
No source is implicitly activated by importing the module or constructing an app.

The initial protocol intentionally returns the existing MVP `SyntheticScenario`
planning DTO and advertises `SYNTHETIC` mode; this is a **current wire-contract
limitation**, not a requirement that all future sources be synthetic. A later
non-fixture execution path needs its own approved planning/evidence type expansion,
not an assertion that an external provider is already implemented.

Generic source-attributed, unverified `TreatmentNotice` and `TreatmentProduct` types
are owned by `sources/notices.py` and exported from the public API. Their timestamps,
nullable geometry and reported chemical attributes are observations, not evidence of
confirmed treatment, safe apiary placement or legal compliance. Planning and analysis
are owned by their existing capabilities; source acquisition must not make policy decisions.

Concrete providers are private to `sources/providers/`. The application composition
root may choose a provider explicitly and inject its collaborators into jobs; ordinary
peer capabilities must depend on `sources.api` contracts rather than concrete adapters.
The current `disabled` provider mode returns no scenarios and never silently falls back
to synthetic evidence. Provider-specific behavior and limitations are documented
in the module docstrings of `providers/synthetic/api.py` and
`providers/saturn/api.py`. No network or PostGIS source ingestion is enabled by
this refactoring.
