# Planning Contract — V01 Synthetic Slice

`melliatlas.planning.api` owns the immutable `TimeWindow`, `CandidateSite`, `SeasonStop`, and `SeasonPlan` models and deterministic `build_season_plan` calculation.

A `TimeWindow` is inclusive and rejects reversed dates. Candidate forage windows are fictional and must be confined to the supported scenario by the caller. The calculation clips candidate windows to the request season, sorts by start date and stable site identifier, and produces non-overlapping ordered stops; at least two are required for a recommendation. Otherwise it returns `None`, never a made-up second stop.

This implementation does not evaluate real ecological exclusions, precautionary areas, legal constraints or travel distances. `SeasonPlan` is a synthetic forage-window proposal, not a safety determination. Future analyzer and agent modules may use these types through the public API without transferring policy ownership.

## V04-01 fictional ecology eligibility policy (partial)

`EcologyZone`, `EcologyOverlap`, `EcologyStatus`, and `SiteAssessment` are task-scoped typed boundaries for a pure demo-only spatial screening calculation. `assess_ecology` maps explicit `DEMO_RESTRICTION` overlaps to `EXCLUDED` and precaution-only overlaps to non-binding `CAUTION`. A non-intersection is `UNKNOWN`, never evidence of actual ecological safety or legal permission. Every result retains rule/evidence IDs and states the lack of verified coverage. The existing `build_season_plan` contract is unchanged; connecting these assessments to candidate filtering and agent replanning remains pending.

## V04-05 fictional treatment preference and source-attributed findings (partial)

`TreatmentProximity`, `TreatmentScreening`, `ReportedTreatmentProduct`, and `TreatmentReview` are provider-neutral, immutable domain result types. `SyntheticScenario.treatment_screening_required` explicitly selects the opt-in offline path. `prefer_sites_away_from_reported_treatments(candidates, screenings)` checks observation identities and coverage of candidates active in the requested season, and withholds candidates with a stated-period field intersection or a near-field finding from an **illustrative** provisional plan. It leaves source identifiers, claimed chemical/crop/hazard-class values, capture and planned UTC timestamps, and uncertainty intact. The policy does not declare a legal exclusion, calculate drift, infer complete notification coverage or certify a remaining site as safe. If fewer than two proposal windows remain, jobs returns insufficient evidence rather than inventing another stop.

The radius and proximity classification are analysis results, not placement permissions. Missing times or geometry are not favorable evidence. Mixed ecology and treatment workflows must not silently skip one analysis; until a combined path exists, such a scenario fails without a plan.


## Synthetic treatment warnings

`TreatmentWarningCode` exposes stable semantic warnings for fictional treatment
screening: unverified notices, unknown coverage, unmodeled drift and demonstration
only. Clients localize these codes; the planning domain does not format end-user
English/Russian messages. This is not a hazard classification or safety decision.
