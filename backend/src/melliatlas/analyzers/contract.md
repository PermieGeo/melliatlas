# Fictional Ecology Spatial Analysis Contract — V04-01 (partial)

`melliatlas.analyzers.find_ecology_overlaps(site, zones)` is a pure, typed point-in-polygon check over explicitly supplied fictional demo zones. Its output is a sorted tuple of `EcologyOverlap` observations; it does not assign legal force, eligibility, source completeness, or real-world safety. GEOS checks geometry validity, and `covers` counts boundary points as intersections. Invalid coordinates, invalid geometry, and missing evidence/rule identifiers fail explicitly.

`planning.assess_ecology(site_id, overlaps)` owns the demo policy: an explicit `DEMO_RESTRICTION` overlap yields `EXCLUDED`, a precaution-only overlap yields `CAUTION`, and absent intersections yield `UNKNOWN` rather than an assertion of eligibility. Decisions retain stable evidence and rule identifiers and an explicit incomplete-coverage disclaimer. The public contracts are limited to this offline pure calculation; no provider reads, authorization claims, candidate filtering, agent replanning, or investigation HTTP integration are implemented in V04-01.


## Fictional pesticide-notice screening — V04-04 (partial)

`melliatlas.analyzers.screen_treatment_notices(site, notices, *, watch_radius_km=7.0)` consumes only the public typed `sources.api.TreatmentNotice` contract and existing `planning.api.CandidateSite`. It compares a proposed site window with the claimed UTC application interval (including a conservative one-day local-date ambiguity margin), a valid WGS84 polygon and a bounded local equirectangular distance approximation. The 7 km default is **a configurable watch radius for a demonstration**, not a legally required buffer, validated bee-flight radius, toxicological model or safe distance. Direct overlap, near-field, outside-watch-radius and missing temporal/spatial evidence are reported separately with source IDs and warnings.

The function does not infer pesticide dispersion, wind direction, verified hazard, compliance, treatment completion or clearance. Even an outside-radius result or empty notice collection is never a proof of safety or source coverage. Broad or polar geometries do not receive fabricated metric precision. No HTTP, SQL, external weather calls or scheduler are introduced; source normalization and planning decisions remain in their owning modules. Future agent integration must preserve the distinction between risk-screening observations and policy-based placement decisions.

## V04-05 treatment observations (partial)

The existing `screen_treatment_notices` now returns provider-neutral planning types and retains each source claim's capture time, optional planned UTC interval, product/crop, reported bee hazard class and optional source URI alongside its site/field proximity. These are unverified *reported* attributes, not independent toxicity judgments. The previous `analyzers.api.TreatmentScreening` and `TreatmentProximity` imports remain public re-exports; the planning capability owns the domain result declarations. No network, wind model or live provider I/O is added.


## Capability layout

`api.py` declares the callable `EcologyOverlapAnalyzer` and
`TreatmentNoticeAnalyzer` Protocols. `ecology.py` and `treatment.py` own the
independent pure algorithms, published by the package facade. Neither analyzer
reads a source or owns storage.
