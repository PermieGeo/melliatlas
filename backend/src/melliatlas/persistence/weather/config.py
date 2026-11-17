"""Read operator-managed weather provider configuration without provider-specific HTTP code.

A weather source is selected only when exactly one configured provider is enabled.
Unknown adapters and unsafe endpoints are rejected later by the composition boundary.
"""

from typing import Final, LiteralString

from melliatlas.persistence.api import ConnectionFactory, WeatherProviderConfig

_WEATHER_SETTINGS_QUERY: Final[LiteralString] = """
    SELECT provider_id, enabled, timeout_seconds, max_body_bytes,
           documentation_url, forecast_url
    FROM melliatlas_weather_provider_config ORDER BY provider_id
"""


def read_weather_configuration(connect: ConnectionFactory) -> WeatherProviderConfig | None:
    """Return the single enabled provider, or None when all configured rows are disabled."""
    connection = connect()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(_WEATHER_SETTINGS_QUERY)
            rows: list[tuple[object, ...]] = []
            while (row := cursor.fetchone()) is not None:
                rows.append(row)
        finally:
            cursor.close()
    finally:
        connection.close()
    if not rows:
        raise ValueError("Weather provider configuration is missing or invalid")
    configured: list[WeatherProviderConfig] = []
    for row in rows:
        match row:
            case (
                str(provider_id),
                bool(enabled),
                int(timeout),
                int(max_body),
                str(source_uri),
                str(forecast_url),
            ):
                pass
            case _:
                raise ValueError("Weather provider configuration is missing or invalid")
        if not provider_id or type(timeout) is not int or type(max_body) is not int:
            raise ValueError("Weather provider configuration is missing or invalid")
        if enabled:
            configured.append(
                WeatherProviderConfig(provider_id, timeout, max_body, source_uri, forecast_url)
            )
    if len(configured) > 1:
        raise ValueError("More than one weather provider is enabled")
    return configured[0] if configured else None
