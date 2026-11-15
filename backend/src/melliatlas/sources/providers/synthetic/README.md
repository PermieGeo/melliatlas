# Synthetic Source Provider

`api.py` implements `sources.api.ScenarioProvider` for offline fixture scenarios in
one explicitly supported RU territory. The fixed forage windows, fictional ecology
zones and historical-shaped spraying notice are **not real source evidence**.
The optional treatment fixture is decoded in `treatments.py` using the offline Saturn
parser, but no network request is made. `SyntheticFixtureProvider.load_treatment_notices`
is a provider-specific adapter used only by the synthetic composition path; it is not
part of the generic provider interface.

The application enables this provider only when `AppSettings(source_provider=SourceProviderMode.SYNTHETIC)`
or `MELLIATLAS_SOURCE_PROVIDER=synthetic` is explicitly selected. Country-specific
source IDs, territory labels and dates belong to the provider, not `sources.api` or
React code. Unsupported countries advertise no executable scenarios.
