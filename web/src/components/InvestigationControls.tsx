import type { ScenarioListing } from "../api/types";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";
import { FieldHelp } from "./FieldHelp";

/** Controls for live-source discovery and optional server-advertised fictional studies. */
interface Props {
  locale: Locale;
  scenarios: ScenarioListing[];
  territory: string;
  scenarioId: string;
  seasonStart: string;
  seasonEnd: string;
  selectedScenario: ScenarioListing | null;
  busy: boolean;
  canSubmit: boolean;
  scenariosMessage: TranslationKey;
  onTerritory: (value: string) => void;
  onScenario: (value: string) => void;
  onSeasonStart: (value: string) => void;
  onSeasonEnd: (value: string) => void;
  onSubmit: () => void;
  canAnalyze: boolean;
  analysisBusy: boolean;
  analysisAttempted: boolean;
  showDemo: boolean;
  onAnalyze: () => void;
  analysisHint: TranslationKey;
  sourceDateStart: string;
  sourceDateEnd: string;
  onSourceDateStart: (value: string) => void;
  onSourceDateEnd: (value: string) => void;
}

/** Render source-backed choices without conflating fictional scenarios with real references. */
export function InvestigationControls(props: Props) {
  const {
    locale,
    scenarios,
    territory,
    scenarioId,
    seasonStart,
    seasonEnd,
    selectedScenario,
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
    <section className="controls" aria-label={tr("workspaceAnalysisTools")}>
      <h2>{tr("workspaceAnalysisTools")}</h2>

      <div className="form-group source-date-range">
        <div className="label-with-help">
          <span>{tr("analysisDateRange")}</span>
          <FieldHelp
            locale={locale}
            label="analysisDateRange"
            explanation="analysisDateMeaning"
          />
        </div>
        <div className="date-range date-range--stacked">
          <label className="date-field">
            <span>{tr("analysisDateStart")}</span>
            <input
              aria-label={tr("analysisDateStart")}
              type="date"
              value={props.sourceDateStart}
              onChange={(event) => props.onSourceDateStart(event.target.value)}
            />
          </label>
          <label className="date-field">
            <span>{tr("analysisDateEnd")}</span>
            <input
              aria-label={tr("analysisDateEnd")}
              type="date"
              value={props.sourceDateEnd}
              onChange={(event) => props.onSourceDateEnd(event.target.value)}
            />
          </label>
        </div>
      </div>
      <div className="label-with-help analysis-help-label">
        <span>{tr("analysisSourcesLabel")}</span>
        <FieldHelp
          locale={locale}
          label="analysisSourcesLabel"
          explanation="workspaceSaturnScope"
        />
      </div>
      <button
        type="button"
        className="primary-button analysis-action"
        disabled={props.analysisBusy}
        aria-busy={props.analysisBusy}
        onClick={props.onAnalyze}
      >
        {tr(props.analysisBusy ? "analysisWorking" : "analysisAction")}
      </button>
      {props.analysisAttempted && !props.canAnalyze && (
        <p className="field-help" role="alert">
          {tr(props.analysisHint)}
        </p>
      )}
      {props.showDemo && scenarios.length > 0 && (
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
                    onChange={(event) =>
                      props.onSeasonStart(event.target.value)
                    }
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
      )}
    </section>
  );
}
