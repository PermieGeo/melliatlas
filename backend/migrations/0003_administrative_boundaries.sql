-- Import verified administrative geometry separately from region identities and provider mappings.
-- PostGIS must be installed on the PostgreSQL server before this migration.
CREATE EXTENSION IF NOT EXISTS postgis;
-- The operator must review dataset provenance and match administrative units before loading.
CREATE TABLE IF NOT EXISTS melliatlas_admin_geometry (
    territory_id TEXT PRIMARY KEY,
    country_code CHAR(2) NOT NULL CHECK (country_code IN ('RU', 'BY')),
    kind TEXT NOT NULL CHECK (kind IN ('region', 'district')),
    region_id TEXT NOT NULL,
    CONSTRAINT admin_geometry_region_fk FOREIGN KEY (region_id, country_code)
        REFERENCES melliatlas_region (id, country_code),
    name TEXT NOT NULL CHECK (length(btrim(name)) > 0),
    external_shape_id TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    reference_uri TEXT NOT NULL,
    reference_license TEXT NOT NULL,
    valid_on DATE NOT NULL,
    boundary GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    CONSTRAINT admin_geometry_valid CHECK (ST_IsValid(boundary)),
    CONSTRAINT admin_geometry_nonempty CHECK (NOT ST_IsEmpty(boundary)),
    CONSTRAINT admin_geometry_region_identity CHECK (
        (kind = 'region' AND territory_id = region_id)
        OR (kind = 'district' AND territory_id <> region_id)
    ),
    CONSTRAINT admin_geometry_shape_unique UNIQUE (country_code, kind, external_shape_id)
);

CREATE INDEX IF NOT EXISTS melliatlas_admin_geometry_parent_idx
    ON melliatlas_admin_geometry (region_id, kind, name);
CREATE INDEX IF NOT EXISTS melliatlas_admin_geometry_boundary_gist
    ON melliatlas_admin_geometry USING GIST (boundary);
