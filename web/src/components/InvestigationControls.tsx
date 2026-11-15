import type {
  Country,
  CountryCode,
  Position,
  ScenarioListing,
  Territory,
} from "../api/types";
import { countryName, t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

/** Inputs for one investigation. Source capabilities and dates are supplied by the API. */
interface Props {
  locale: Locale;
  countries: Country[];
  country: CountryCode;
  regions: Territory[];
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
  scenariosMessage: TranslationKey;
  reopenId: string;
  onCountry: (value: CountryCode) => void;
  onTerritory: (value: string) => void;
  onScenario: (value: string) => void;
  onSeasonStart: (value: string) => void;
  onSeasonEnd: (value: string) => void;
  onClearPoint: () => void;
  onSubmit: () => void;
  onReopenId: (value: string) => void;
  onReopen: () => void;
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
      {selectedScenario?.source_mode === "SYNTHETIC" && (
        <div className="demo-notice" role="note">
          <strong>{tr("syntheticTitle")}</strong> {tr("syntheticDisclaimer")}
        </div>
      )}
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
          {regions
            .filter(
              (item) => !syntheticTerritories.some(([id]) => id === item.id),
            )
            .map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
        </select>
        <p className="field-help" role="status">
          {tr(props.referenceMessage)}
        </p>
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
        className="primary-button"
        disabled={!canSubmit}
        onClick={props.onSubmit}
      >
        {busy ? tr("running") : tr("run")} <span aria-hidden="true">↗</span>
      </button>
      {!canSubmit && !busy && <p className="field-help">{tr("submitHelp")}</p>}
      <div className="reopen">
        <label htmlFor="reopen-id">{tr("reopen")}</label>
        <div className="reopen-row">
          <input
            id="reopen-id"
            placeholder={tr("reopenPlaceholder")}
            value={props.reopenId}
            onChange={(event) => props.onReopenId(event.target.value)}
          />
          <button
            type="button"
            disabled={busy || !/^[0-9a-fA-F-]{36}$/.test(props.reopenId.trim())}
            onClick={props.onReopen}
          >
            {tr("open")}
          </button>
        </div>
        <p className="field-help">{tr("reopenHelp")}</p>
      </div>
    </aside>
  );
}
