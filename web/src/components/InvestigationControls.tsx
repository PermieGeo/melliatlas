import type {
  Country,
  CountryCode,
  Position,
  ScenarioListing,
  Territory,
} from "../api/types";
import { ReferenceControls } from "./ReferenceControls";
import type { TerritoryNavigation } from "../hooks/useTerritoryReference";
import { countryName, t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

/** Controls for live-source discovery and optional server-advertised fictional studies. */
interface Props {
  locale: Locale;
  countries: Country[];
  country: CountryCode;
  regions: Territory[];
  referenceNavigation: TerritoryNavigation;
  scenarios: ScenarioListing[];
  territory: string;
  scenarioId: string;
  seasonStart: string;
  seasonEnd: string;
  selectedScenario: ScenarioListing | null;
  point: Position | null;
  busy: boolean;
  canSubmit: boolean;
  countryMessage: TranslationKey;
  referenceMessage: TranslationKey;
  onRetryRegions: () => void;
  scenariosMessage: TranslationKey;
  onCountry: (value: CountryCode) => void;
  onTerritory: (value: string) => void;
  onScenario: (value: string) => void;
  onSeasonStart: (value: string) => void;
  onSeasonEnd: (value: string) => void;
  onClearPoint: () => void;
  onSubmit: () => void;
  canAnalyze: boolean;
  onAnalyze: () => void;
  analysisHint: TranslationKey;
}

/** Render source-backed choices without conflating fictional scenarios with real references. */
export function InvestigationControls(props: Props) {
  const {
    locale,
    countries,
    country,
    regions,
    scenarios,
    territory,
    scenarioId,
    seasonStart,
    seasonEnd,
    selectedScenario,
    point,
    busy,
    canSubmit,
  } = props;
  const tr = (key: TranslationKey, values?: Record<string, string | number>) =>
    t(locale, key, values);
  const syntheticTerritories = Array.from(
    new Map(
      scenarios.map((item) => [item.territory_id, item.territory_name]),
    ).entries(),
  );
  return (
    <aside className="controls" aria-label={tr("setup")}>
      <div className="eyebrow">{tr("setup")}</div>
      <h1>{tr("heading")}</h1>
      <p className="lead">{tr("introduction")}</p>
      <div className="form-group">
        <label htmlFor="country">{tr("country")}</label>
        <select
          id="country"
          value={country}
          onChange={(event) => props.onCountry(event.target.value)}
          disabled={countries.length === 0}
        >
          {countries.length === 0 && (
            <option value="">{tr("selectCountry")}</option>
          )}
          {countries.map((item) => (
            <option key={item.code} value={item.code}>
              {countryName(locale, item.code, item.name)}
            </option>
          ))}
        </select>
        {countries.length === 0 && (
          <p className="field-help" role="status">
            {tr(props.countryMessage)}
          </p>
        )}
      </div>
      <ReferenceControls
        locale={locale}
        regions={regions}
        navigation={props.referenceNavigation}
        catalogMessage={props.referenceMessage}
        onRetryRegions={props.onRetryRegions}
      />
      <div className="form-group">
        <label>{tr("startingPoint")}</label>
        <p className="field-help">{tr("pointHelp")}</p>
        {point && (
          <div className="point-row">
            <span>
              {tr("pointSelected", {
                lat: point.latitude.toFixed(3),
                lon: point.longitude.toFixed(3),
              })}
            </span>
            <button type="button" onClick={props.onClearPoint}>
              {tr("clear")}
            </button>
          </div>
        )}
      </div>
      <button
        type="button"
        className="primary-button analysis-action"
        disabled={!props.canAnalyze}
        onClick={props.onAnalyze}
      >
        {tr("analysisAction")}
      </button>
      {!props.canAnalyze && (
        <p className="field-help" role="status">
          {tr(props.analysisHint)}
        </p>
      )}
      <details className="synthetic-workflow">
        <summary>{tr("demoWorkflowHeading")}</summary>
        {scenarios.length === 0 ? (
          <p className="field-help" role="status">
            {props.scenariosMessage === "noScenarios"
              ? tr("demoWorkflowUnavailable")
              : tr(props.scenariosMessage)}
          </p>
        ) : (
          <>
            {selectedScenario?.source_mode === "SYNTHETIC" && (
              <div className="demo-notice" role="note">
                <strong>{tr("syntheticTitle")}</strong>{" "}
                {tr("syntheticDisclaimer")}
              </div>
            )}
            <div className="form-group">
              <label htmlFor="territory">{tr("territory")}</label>
              <select
                id="territory"
                value={territory}
                onChange={(event) => props.onTerritory(event.target.value)}
              >
                <option value="">{tr("selectTerritory")}</option>
                {syntheticTerritories.map(([id, name]) => (
                  <option key={`synthetic:${id}`} value={id}>
                    {tr("syntheticMode")} · {name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="scenario">{tr("scenario")}</label>
              <select
                id="scenario"
                value={scenarioId}
                onChange={(event) => props.onScenario(event.target.value)}
              >
                <option value="">{tr("selectScenario")}</option>
                {scenarios
                  .filter((item) => item.territory_id === territory)
                  .map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
              </select>
              <p className="field-help" role="status">
                {tr(props.scenariosMessage)}
              </p>
            </div>
            <div className="form-group">
              <label>{tr("season")}</label>
              <div className="date-range">
                <input
                  aria-label={tr("seasonStart")}
                  type="date"
                  value={seasonStart}
                  min={selectedScenario?.season_start}
                  max={selectedScenario?.season_end}
                  disabled={selectedScenario === null}
                  onChange={(event) => props.onSeasonStart(event.target.value)}
                />
                <span>—</span>
                <input
                  aria-label={tr("seasonEnd")}
                  type="date"
                  value={seasonEnd}
                  min={selectedScenario?.season_start}
                  max={selectedScenario?.season_end}
                  disabled={selectedScenario === null}
                  onChange={(event) => props.onSeasonEnd(event.target.value)}
                />
              </div>
              <p className="field-help">
                {selectedScenario
                  ? tr("seasonRange", {
                      start: selectedScenario.season_start,
                      end: selectedScenario.season_end,
                    })
                  : tr("seasonNoSource")}
              </p>
            </div>
            <button
              type="button"
              className="primary-button"
              disabled={!canSubmit}
              onClick={props.onSubmit}
            >
              {busy ? tr("running") : tr("run")}{" "}
              <span aria-hidden="true">↗</span>
            </button>
            {!canSubmit && !busy && (
              <p className="field-help">{tr("submitHelp")}</p>
            )}
          </>
        )}
      </details>
    </aside>
  );
}
