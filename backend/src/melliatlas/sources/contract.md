# Synthetic Source Contract — V01 and opt-in V04-03

`SyntheticFixtureProvider.load` performs no I/O and returns a recognized, explicitly fictional `RU` scenario or `None` for unsupported `(country, territory_id, scenario_id)` combinations. It does not invent general-purpose catalog completeness or provide live weather, Saturn or publication access.

The fixture contains three fictional candidate sites, three dated forage windows, stable evidence IDs, the `FIXTURE` source mode, a synthetic reference marker and explicit uncertainty/limitations. Data is recalculated from static values for each load and is not a substitute for a versioned reference import or a persisted source cache.

The opt-in `synthetic-ru-2026-v04-ecology` scenario preserves the V01 scenario unchanged and adds one fictional alternative plus two separately identified, explicitly fictional ecology polygons. Each ecology zone's evidence ID is backed by a `FIXTURE` `EvidenceSummary` with an uncertainty note; neither zone establishes real legal prohibitions or environmental coverage. The additively optional `SyntheticScenario.ecology_zones` field is empty for V01.
