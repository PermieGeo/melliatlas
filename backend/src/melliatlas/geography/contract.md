# Geography Public Contract

`melliatlas.geography` is the public, provider-neutral facade for WGS84 position invariants, distance helpers, and bounded analysis rectangles. It performs no I/O.

`make_analysis_bounds()` accepts a center in longitude/latitude order and strictly positive width/height, each at most 30 km. It returns an immutable pair of latitude bounds and one or two non-wrapping longitude intervals. The two-interval form preserves rectangles crossing the antimeridian. Invalid coordinates, non-finite dimensions, polar-crossing bounds, and unsupported sizes raise `ValueError` before any persistence access.

For rectangles this small, longitude/latitude offsets use local WGS84 ellipsoid curvature radii. Sides follow meridians and parallels; `nominal_area_km2` is the requested width multiplied by height, **not** a surveyed equal-area surface or a pesticide-exposure buffer. Exact types and signatures are exported through `melliatlas.geography.__init__`.
