-- Apply against a dedicated PostgreSQL database with PostGIS privileges.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS melliatlas_completed_investigations (
    id UUID PRIMARY KEY,
    payload JSONB NOT NULL,
    reference_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL,
    site_points GEOMETRY(MULTIPOINT, 4326),
    CONSTRAINT completed_investigation_status CHECK (
        (payload ->> 'status' = 'COMPLETED') IS TRUE
    ),
    CONSTRAINT completed_investigation_id CHECK (
        (payload ->> 'id' = id::text) IS TRUE
    ),
    CONSTRAINT completed_investigation_timestamps CHECK (completed_at >= created_at),
    CONSTRAINT completed_investigation_site_points_valid CHECK (
        site_points IS NULL OR ST_IsValid(site_points)
    )
);

CREATE INDEX IF NOT EXISTS melliatlas_completed_investigations_site_points_gist
    ON melliatlas_completed_investigations USING GIST (site_points);
