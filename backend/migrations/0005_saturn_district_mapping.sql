-- Operator-reviewed Saturn identifiers never derive from geoBoundaries shape IDs.
-- This mapping is intentionally empty until a district identity is independently verified.
CREATE TABLE IF NOT EXISTS melliatlas_source_saturn_district (
    district_id TEXT PRIMARY KEY REFERENCES melliatlas_admin_geometry(territory_id),
    provider_district_code INTEGER NOT NULL CHECK (provider_district_code BETWEEN 1 AND 999999),
    source_uri TEXT NOT NULL CHECK (source_uri LIKE 'https://%'),
    verified_at TIMESTAMPTZ NOT NULL
);
