# Analyzer Rules

Inherits root and backend guidance. Analyzers **transform typed evidence into explainable typed artifacts**.

- Declare input/output artifact kinds, dependencies, algorithm ID/version, resource limits, supported geography, and uncertainty semantics before registration.
- Keep deterministic geographic/statistical logic testable without network or LLM access. Separate model adapters from analysis algorithms; do not hide a fetch inside a spatial calculation.
- Preserve input evidence IDs, versions, temporal/spatial coverage, assumptions, and output limitations. Do not assert precision, model accuracy, bee safety, or actual spraying without independently validated evidence.
- Use WGS84/GeoJSON explicitly for exchange; verify coordinate order, CRS, units, geometry validity, and appropriate PostGIS computations when implemented.
- Cover missing/conflicting data, zero coverage, boundaries, non-Polygon geometries, faulty model output, and deterministic synthetic comparisons. An unavailable analysis is not a successful zero-risk result.
