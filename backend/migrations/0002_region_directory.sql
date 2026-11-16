-- Apply once after 0001 to the same PostgreSQL database.
-- Administrative identity is provider-independent; no regional geometry is implied.
CREATE TABLE IF NOT EXISTS melliatlas_region (
    id TEXT PRIMARY KEY,
    country_code CHAR(2) NOT NULL CHECK (country_code IN ('RU', 'BY')),
    iso_3166_2 TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL CHECK (length(btrim(name)) > 0),
    name_en TEXT NOT NULL CHECK (length(btrim(name_en)) > 0),
    reference_id TEXT NOT NULL,
    reference_uri TEXT NOT NULL,
    reference_license TEXT NOT NULL,
    valid_on DATE NOT NULL,
    CONSTRAINT region_country_iso_match CHECK (split_part(iso_3166_2, '-', 1) = country_code),
    CONSTRAINT region_canonical_id CHECK (
        id = lower(country_code) || ':region:' || lower(split_part(iso_3166_2, '-', 2))
    ),
    CONSTRAINT region_country_identity UNIQUE (id, country_code)
);

CREATE INDEX IF NOT EXISTS melliatlas_region_country_idx
    ON melliatlas_region (country_code, name);

-- Saturn identifiers are separate foreign keys; this table cannot contain BY mappings.
CREATE TABLE IF NOT EXISTS melliatlas_source_saturn (
    region_id TEXT PRIMARY KEY,
    country_code CHAR(2) NOT NULL DEFAULT 'RU' CHECK (country_code = 'RU'),
    subject_id INTEGER NOT NULL UNIQUE CHECK (subject_id > 0 AND subject_id <= 999999),
    oktmo_code TEXT CHECK (oktmo_code IS NULL OR oktmo_code ~ '^[0-9]{8}$'),
    source_uri TEXT NOT NULL,
    capture_sha256 TEXT CHECK (capture_sha256 IS NULL OR capture_sha256 ~ '^[0-9a-f]{64}$'),
    verified_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT source_saturn_region_fk FOREIGN KEY (region_id, country_code)
        REFERENCES melliatlas_region (id, country_code)
);
