"""Read operational weather settings from the optional configured database.

The persistence adapter does not know a forecast provider's HTTP internals.
The composition root validates these values against the provider's policy.
A missing migration or unavailable database fails closed when DB mode is chosen.
"""

from typing import Final, LiteralString

from melliatlas.persistence.api import ConnectionFactory

_WEATHER_SETTINGS_QUERY: Final[LiteralString] = """
    SELECT enabled, timeout_seconds, max_body_bytes, documentation_url
    FROM melliatlas_weather_provider_config WHERE provider_id = %s
"""


def read_weather_configuration(connect: ConnectionFactory) -> tuple[bool, int, int, str]:
    connection = connect()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(_WEATHER_SETTINGS_QUERY, ("open-meteo",))
            row = cursor.fetchone()
        finally:
            cursor.close()
    finally:
        connection.close()
    if row is None or len(row) != 4:
        raise ValueError("Weather provider configuration is missing or invalid")
    enabled, timeout, max_body, documentation = row
    if (
        type(enabled) is not bool
        or type(timeout) is not int
        or type(max_body) is not int
        or not isinstance(documentation, str)
    ):
        raise ValueError("Weather provider configuration is missing or invalid")
    return enabled, timeout, max_body, documentation
