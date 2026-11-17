-- Store operator-reviewed weather URLs in PostgreSQL, not in application source.
-- The Python adapter still validates each URL against its approved provider host and path.
ALTER TABLE melliatlas_weather_provider_config
    ADD COLUMN IF NOT EXISTS forecast_url TEXT;

UPDATE melliatlas_weather_provider_config
SET forecast_url = 'https://api.open-meteo.com/v1/forecast'
WHERE provider_id = 'open-meteo' AND forecast_url IS NULL;

ALTER TABLE melliatlas_weather_provider_config
    ALTER COLUMN forecast_url SET NOT NULL;

-- A new adapter is required before the application can use another provider's wire format.
ALTER TABLE melliatlas_weather_provider_config
    DROP CONSTRAINT IF EXISTS melliatlas_weather_provider_config_provider_id_check;
ALTER TABLE melliatlas_weather_provider_config
    DROP CONSTRAINT IF EXISTS melliatlas_weather_provider_config_documentation_url_check;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'melliatlas_weather_provider_config'::regclass
          AND conname = 'melliatlas_weather_forecast_https'
    ) THEN
        ALTER TABLE melliatlas_weather_provider_config
            ADD CONSTRAINT melliatlas_weather_forecast_https
            CHECK (forecast_url LIKE 'https://%');
    END IF;
END $$;
