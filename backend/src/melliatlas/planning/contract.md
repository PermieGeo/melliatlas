# Planning Contract — V01 Synthetic Slice

`melliatlas.planning.api` owns the immutable `TimeWindow`, `CandidateSite`, `SeasonStop`, and `SeasonPlan` models and deterministic `build_season_plan` calculation.

A `TimeWindow` is inclusive and rejects reversed dates. Candidate forage windows are fictional and must be confined to the supported scenario by the caller. The calculation clips candidate windows to the request season, sorts by start date and stable site identifier, and produces non-overlapping ordered stops; at least two are required for a recommendation. Otherwise it returns `None`, never a made-up second stop.

This implementation does not evaluate real ecological exclusions, precautionary areas, legal constraints or travel distances. `SeasonPlan` is a synthetic forage-window proposal, not a safety determination. Future analyzer and agent modules may use these types through the public API without transferring policy ownership.
