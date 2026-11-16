# Source Provider Contract

The public capability boundary is `melliatlas.sources.api`: `ScenarioProvider` is a
structural Python `Protocol`, and `ScenarioListing` advertises the identity, country,
territory, source mode, inclusive supported season and default status of an executable
scenario. `ScenarioProvider.load(country=..., territory_id=..., scenario_id=...)`
returns a typed scenario or `None` for an unsupported combination;
`list_scenarios(country)` returns only scenarios the provider can actually load.
No source is implicitly activated by importing the module or constructing an app.

The initial protocol intentionally returns the existing MVP `SyntheticScenario`
planning DTO and advertises `SYNTHETIC` mode; this is a **current wire-contract
limitation**, not a requirement that all future sources be synthetic. A later
non-fixture execution path needs its own approved planning/evidence type expansion,
not an assertion that an external provider is already implemented.

Generic source-attributed, unverified `TreatmentNotice` and `TreatmentProduct` types
are owned by `sources/notices.py` and exported from the public API. Their timestamps,
nullable geometry and reported chemical attributes are observations, not evidence of
confirmed treatment, safe apiary placement or legal compliance. Planning and analysis
are owned by their existing capabilities; source acquisition must not make policy decisions.

Concrete providers are private to `sources/providers/`. The application composition
root may choose a provider explicitly and inject its collaborators into jobs; ordinary
peer capabilities must depend on `sources.api` contracts rather than concrete adapters.
The current `disabled` provider mode returns no scenarios and never silently falls back
to synthetic evidence. Provider-specific behavior and limitations are documented
in the module docstrings of `providers/synthetic/api.py` and
`providers/saturn/api.py`. No network or PostGIS source ingestion is enabled by
this refactoring.

## Opt-in public treatment-notice reads (experimental)

`TreatmentNoticeReader.read_page(country, region_code, page_number)` is a small,
source-neutral on-demand port. `TreatmentNoticePage` retains the UTC capture time,
source, country, upstream region code, pagination and every recognized notice.
`SourceReadError` communicates unreadable or malformed upstream data; it must not
be interpreted as an empty notice collection. A notice distinguishes `LIVE`
with `synthetic=False` from `FIXTURE` with `synthetic=True`.

The single known Saturn adapter is RU-only, disabled by default, and never
part of synthetic scenario or planner composition. The request is bounded to
one page, is user-initiated and preserves unknown location/time evidence. A
publisher's public-facing webpage does not guarantee an approved automated
interface or permission to reuse its data. Full-source coverage and drift
analysis remain unimplemented.

## Opt-in hourly weather forecast (experimental)

`WeatherForecastReader.forecast(latitude, longitude)` is a provider-neutral,
read-only port for an explicitly selected WGS84 point. The return value retains
the provider, retrieval timestamp, original coordinates, provider grid point,
24 consecutive UTC forecast hours, nullable physical variables and uncertainty.
Missing hourly values stay `None`, never zero. `SourceReadError` means unknown
weather availability, not calm wind or no pesticide exposure.

The Open-Meteo implementation decodes only one 24-hour forecast with 10-m wind
speed/direction, gusts and precipitation. Provider-owned `open_meteo/http.py`
uses a shared fixed-origin transport helper; only the API composition root can
instantiate it. PostgreSQL `0004_weather_provider_configuration.sql` stores an
optional enable/timeout/byte budget and allowlisted attribution URL. The ASGI
entry point reads that row only when a database and the explicit weather live
flag are both configured; missing configuration fails closed. The 24-hour UTC
wire contract and source HTTP origin are not database overrides. No advection, spray drift, safety rating, automatic refresh or cached forecasts
are provided. This source does not require a synthetic scenario and is usable
independently of the country-specific Saturn notice reader.
