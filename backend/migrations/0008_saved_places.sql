-- Private, owner-scoped saved places. Apply only to a separately authorized PostgreSQL database.
-- The application does not migrate databases at startup or expose saved-place HTTP routes.
CREATE TABLE IF NOT EXISTS melliatlas_saved_place (
    id UUID PRIMARY KEY,
    owner_id UUID NOT NULL CHECK (owner_id <> '00000000-0000-0000-0000-000000000000'::uuid),
    name TEXT NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 120),
    country_code CHAR(2) NOT NULL CHECK (country_code IN ('RU', 'BY')),
    region_id TEXT NOT NULL,
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    width_km DOUBLE PRECISION NOT NULL CHECK (width_km > 0 AND width_km <= 30),
    height_km DOUBLE PRECISION NOT NULL CHECK (height_km > 0 AND height_km <= 30),
    boundary GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision > 0),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL CHECK (updated_at >= created_at),
    CONSTRAINT saved_place_region_fk FOREIGN KEY (region_id, country_code)
        REFERENCES melliatlas_region (id, country_code),
    CONSTRAINT saved_place_geometry_valid CHECK (ST_IsValid(boundary) AND NOT ST_IsEmpty(boundary))
);

CREATE INDEX IF NOT EXISTS melliatlas_saved_place_owner_order_idx
    ON melliatlas_saved_place (owner_id, updated_at DESC, id);
CREATE INDEX IF NOT EXISTS melliatlas_saved_place_boundary_gist
    ON melliatlas_saved_place USING GIST (boundary);
