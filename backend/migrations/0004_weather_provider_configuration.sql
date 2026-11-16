-- Weather source settings are independent of country and Saturn district mapping.
-- Live forecasts still require the explicit MELLIATLAS_WEATHER_LIVE_ENABLED gate.
-- Keep the current 24-hour UTC metric response schema as a fixed API contract.
CREATE TABLE IF NOT EXISTS melliatlas_weather_provider_config (
    provider_id TEXT PRIMARY KEY CHECK (provider_id = 'open-meteo'),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    documentation_url TEXT NOT NULL DEFAULT 'https://open-meteo.com/en/docs'
        CHECK (documentation_url LIKE 'https://open-meteo.com/%'),
    timeout_seconds SMALLINT NOT NULL DEFAULT 8 CHECK (timeout_seconds BETWEEN 1 AND 15),
    max_body_bytes INTEGER NOT NULL DEFAULT 100000
        CHECK (max_body_bytes BETWEEN 1024 AND 100000)
);

INSERT INTO melliatlas_weather_provider_config (provider_id)
VALUES ('open-meteo') ON CONFLICT DO NOTHING;
