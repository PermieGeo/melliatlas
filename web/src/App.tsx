import { useEffect, useState } from "react";
import { listCountries, listRegions, listScenarios } from "./api/client";
import type {
  Country,
  CountryCode,
  Position,
  ScenarioListing,
  Territory,
} from "./api/types";
import { InvestigationControls } from "./components/InvestigationControls";
import { EvidencePanel } from "./components/EvidencePanel";
import { MapPanel } from "./components/MapPanel";
import { Timeline } from "./components/Timeline";
import { useInvestigation } from "./hooks/useInvestigation";
import { useTerritoryReference } from "./hooks/useTerritoryReference";
import { t } from "./i18n";
import type { Locale, TranslationKey } from "./i18n";

const PREFERRED_COUNTRY: CountryCode = "RU";

/** Top-level composition: server-backed source selection plus a cancellable investigation. */
export default function App() {
  const [locale, setLocale] = useState<Locale>("ru");
  const [countries, setCountries] = useState<Country[]>([]);
  const [country, setCountry] = useState<CountryCode>("");
  const [regions, setRegions] = useState<Territory[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioListing[]>([]);
  const [territory, setTerritory] = useState("");
  const [scenarioId, setScenarioId] = useState("");
  const [seasonStart, setSeasonStart] = useState("");
  const [seasonEnd, setSeasonEnd] = useState("");
  const [countryMessage, setCountryMessage] =
    useState<TranslationKey>("loadingCountries");
  const [referenceMessage, setReferenceMessage] =
    useState<TranslationKey>("loadingRegions");
  const [scenariosMessage, setScenariosMessage] =
    useState<TranslationKey>("loadingScenarios");
  const [point, setPoint] = useState<Position | null>(null);
  const [showTiles, setShowTiles] = useState(false);
  const [reopenId, setReopenId] = useState("");
  const investigation = useInvestigation();
  const referenceNavigation = useTerritoryReference(country, regions);
  const { reset } = investigation;
  const tr = (key: TranslationKey, values?: Record<string, string | number>) =>
    t(locale, key, values);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  useEffect(() => {
    const controller = new AbortController();
    void listCountries(controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (response.kind === "ok") {
        setCountries(response.data);
        setCountryMessage(
          response.data.length === 0 ? "countriesEmpty" : "selectCountry",
        );
        setCountry(
          response.data.find((item) => item.code === PREFERRED_COUNTRY)?.code ??
            response.data[0]?.code ??
            "",
        );
      } else {
        setCountries([]);
        setCountry("");
        setCountryMessage("countriesFailure");
      }
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setRegions([]);
    setReferenceMessage("loadingRegions");
    if (!country) return () => controller.abort();
    void listRegions(country, controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (response.kind === "ok") {
        if (
          response.data.some(
            (item) => item.country !== country || item.kind !== "region",
          )
        ) {
          setReferenceMessage("regionsFailure");
          return;
        }
        setRegions(response.data);
        setReferenceMessage(
          response.data.length === 0 ? "emptyRegions" : "availableRegions",
        );
      } else {
        setReferenceMessage(
          response.status === 503 ? "unavailableRegions" : "regionsFailure",
        );
      }
    });
    return () => controller.abort();
  }, [country]);

  useEffect(() => {
    const controller = new AbortController();
    setScenarios([]);
    setTerritory("");
    setScenarioId("");
    setSeasonStart("");
    setSeasonEnd("");
    setScenariosMessage("loadingScenarios");
    if (!country) return () => controller.abort();
    void listScenarios(country, controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (response.kind === "error") {
        setScenariosMessage("scenarioFailure");
        return;
      }
      // Do not trust a cross-country descriptor even when the wire shape is valid.
      if (response.data.some((item) => item.country !== country)) {
        setScenariosMessage("scenarioFailure");
        return;
      }
      setScenarios(response.data);
      setScenariosMessage(
        response.data.length === 0 ? "noScenarios" : "selectScenario",
      );
      const preferred =
        response.data.find((item) => item.is_default) ?? response.data[0];
      if (preferred) {
        setTerritory(preferred.territory_id);
        setScenarioId(preferred.id);
        setSeasonStart(preferred.season_start);
        setSeasonEnd(preferred.season_end);
      }
    });
    return () => controller.abort();
  }, [country]);

  const selectedScenario =
    scenarios.find(
      (item) =>
        item.id === scenarioId &&
        item.country === country &&
        item.territory_id === territory,
    ) ?? null;
  const canSubmit =
    !investigation.busy &&
    countries.some((item) => item.code === country) &&
    selectedScenario !== null &&
    !!seasonStart &&
    !!seasonEnd &&
    seasonStart >= selectedScenario.season_start &&
    seasonEnd <= selectedScenario.season_end &&
    seasonStart <= seasonEnd;

  const chooseCountry = (value: CountryCode) => {
    if (!countries.some((item) => item.code === value)) return;
    reset();
    setPoint(null);
    setCountry(value);
    setTerritory("");
    setScenarioId("");
  };
  const chooseTerritory = (value: string) => {
    reset();
    setTerritory(value);
    const preferred =
      scenarios.find(
        (item) => item.territory_id === value && item.is_default,
      ) ?? scenarios.find((item) => item.territory_id === value);
    setScenarioId(preferred?.id ?? "");
    setSeasonStart(preferred?.season_start ?? "");
    setSeasonEnd(preferred?.season_end ?? "");
  };
  const chooseScenario = (value: string) => {
    reset();
    const chosen = scenarios.find(
      (item) => item.id === value && item.territory_id === territory,
    );
    setScenarioId(chosen?.id ?? "");
    setSeasonStart(chosen?.season_start ?? "");
    setSeasonEnd(chosen?.season_end ?? "");
  };
  const begin = () => {
    if (!canSubmit || !selectedScenario) return;
    void investigation.begin({
      country: selectedScenario.country,
      territory_id: selectedScenario.territory_id,
      scenario_id: selectedScenario.id,
      season_start: seasonStart,
      season_end: seasonEnd,
      ...(point ? { starting_point: point } : {}),
    });
  };
  const stops = investigation.result?.plan?.stops ?? [];

  return (
    <div className="app-shell">
      <header className="masthead">
        <div className="brand">
          <span className="brand-icon" aria-hidden="true">
            ✳
          </span>
          <span>
            Melli<span className="brand-accent">Atlas</span>
          </span>
        </div>
        <div className="header-context">
          <span className="status-dot" /> {tr("headerContext")}
          {selectedScenario?.source_mode === "SYNTHETIC" && (
            <>
              <span className="header-separator">/</span> {tr("syntheticMode")}
            </>
          )}
        </div>
        <div className="header-actions">
          <label htmlFor="language">{tr("language")}</label>
          <select
            id="language"
            value={locale}
            onChange={(event) =>
              setLocale(event.target.value === "en" ? "en" : "ru")
            }
          >
            <option value="ru">RU</option>
            <option value="en">EN</option>
          </select>
          <span className="header-version">MVP · W01</span>
        </div>
      </header>
      <div className="workspace">
        <InvestigationControls
          locale={locale}
          countries={countries}
          country={country}
          regions={regions}
          referenceNavigation={referenceNavigation}
          scenarios={scenarios}
          territory={territory}
          scenarioId={scenarioId}
          seasonStart={seasonStart}
          seasonEnd={seasonEnd}
          selectedScenario={selectedScenario}
          point={point}
          busy={investigation.busy}
          canSubmit={canSubmit}
          countryMessage={countryMessage}
          referenceMessage={referenceMessage}
          scenariosMessage={scenariosMessage}
          reopenId={reopenId}
          onCountry={chooseCountry}
          onTerritory={chooseTerritory}
          onScenario={chooseScenario}
          onSeasonStart={(value) => {
            reset();
            setSeasonStart(value);
          }}
          onSeasonEnd={(value) => {
            reset();
            setSeasonEnd(value);
          }}
          onClearPoint={() => setPoint(null)}
          onSubmit={begin}
          onReopenId={setReopenId}
          onReopen={() => void investigation.begin(reopenId.trim())}
        />
        <main className="canvas-column">
          <section className="map-section" aria-label={tr("mapLabel")}>
            <div className="section-header">
              <div>
                <span className="eyebrow">{tr("mapSpace")}</span>
                <h2>{tr("mapHeading")}</h2>
              </div>
              <label className="tile-switch">
                <input
                  type="checkbox"
                  checked={showTiles}
                  onChange={(event) => setShowTiles(event.target.checked)}
                />{" "}
                {tr("basemap")}
                <span className="tile-info" title={tr("basemapPrivacy")}>
                  ⓘ
                </span>
              </label>
            </div>
            <MapPanel
              locale={locale}
              stops={stops}
              selectedId={investigation.selectedSite}
              startingPoint={point}
              showTiles={showTiles}
              referenceGeometry={referenceNavigation.geometry}
              onSelect={investigation.setSelectedSite}
              onPoint={setPoint}
            />
          </section>
          {investigation.notice && (
            <div
              className={`message message-${investigation.notice.kind}`}
              role="status"
            >
              {tr(investigation.notice.key, investigation.notice.values)}
            </div>
          )}
          {investigation.result && (
            <div className="result-banner" aria-live="polite">
              <strong>
                {investigation.result.status === "COMPLETED"
                  ? tr(investigation.result.plan ? "planReady" : "noPlan")
                  : tr("status", { status: investigation.result.status })}
              </strong>
              <span>
                {investigation.result.plan
                  ? tr("stopsCount", {
                      count: investigation.result.plan.stops.length,
                      moves: investigation.result.plan.relocations,
                    })
                  : (investigation.result.outcome ?? tr("awaiting"))}
              </span>
              <span className="result-id">ID: {investigation.result.id}</span>
            </div>
          )}
          <Timeline
            locale={locale}
            stops={stops}
            seasonStart={
              investigation.result?.request.season_start ?? seasonStart
            }
            seasonEnd={investigation.result?.request.season_end ?? seasonEnd}
            selectedId={investigation.selectedSite}
            onSelect={investigation.setSelectedSite}
          />
        </main>
        <EvidencePanel
          locale={locale}
          result={investigation.result}
          selectedId={investigation.selectedSite}
        />
      </div>
      <footer className="footer-note">{tr("footer")}</footer>
    </div>
  );
}
