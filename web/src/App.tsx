import { useEffect, useRef, useState } from "react";
import {
  listCountries,
  listRegions,
  listScenarios,
  resolveTerritoryPoint,
} from "./api/client";
import type {
  Country,
  CountryCode,
  Position,
  SaturnNotice,
  ScenarioListing,
  Territory,
} from "./api/types";
import { InvestigationControls } from "./components/InvestigationControls";
import { WorkspaceHeader } from "./components/WorkspaceHeader";
import { PlaceSearchToolbar } from "./components/PlaceSearchToolbar";
import { EvidencePanel } from "./components/EvidencePanel";
import { MapPanel } from "./components/MapPanel";
import { AreaDraftPanel } from "./components/AreaDraftPanel";
import { Timeline } from "./components/Timeline";
import { LiveAreaAnalysis } from "./components/LiveAreaAnalysis";
import type { AreaAnalysisRequest } from "./components/LiveAreaAnalysis";
import { isInsideArea, representativePoint } from "./geo/selection";
import { updateSourceDateRange, validSourceDateRange } from "./geo/dateRange";
import {
  readTerritoryPreference,
  saveTerritoryPreference,
} from "./geo/territoryPreference";
import { WeatherPanel } from "./components/WeatherPanel";
import {
  readSourceDatePreference,
  saveSourceDatePreference,
} from "./geo/sourceDatePreference";
import { useInvestigation } from "./hooks/useInvestigation";
import { useAreaDraft } from "./hooks/useAreaDraft";
import { useAreaDistrictBoundary } from "./hooks/useAreaDistrictBoundary";
import { useTerritoryReference } from "./hooks/useTerritoryReference";
import { t } from "./i18n";
import type { Locale, TranslationKey } from "./i18n";

const PREFERRED_COUNTRY: CountryCode = "RU";

/** Top-level composition: server-backed source selection plus a cancellable investigation. */
export default function App() {
  const [locale, setLocale] = useState<Locale>("ru");
  const [countries, setCountries] = useState<Country[]>([]);
  const [country, setCountry] = useState<CountryCode>("");
  const [regionCatalog, setRegionCatalog] = useState<{
    country: CountryCode;
    regions: Territory[];
    message: TranslationKey;
  }>({ country: "", regions: [], message: "loadingRegions" });
  const [regionRequestVersion, setRegionRequestVersion] = useState(0);
  const [scenarios, setScenarios] = useState<ScenarioListing[]>([]);
  const [territory, setTerritory] = useState("");
  const [scenarioId, setScenarioId] = useState("");
  const [seasonStart, setSeasonStart] = useState("");
  const [seasonEnd, setSeasonEnd] = useState("");
  const [sourceRange, setSourceRange] = useState(readSourceDatePreference);
  const [analysisAttempted, setAnalysisAttempted] = useState(false);
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [weatherRefresh, setWeatherRefresh] = useState(0);
  const showDeveloperDemo = window.location.pathname === "/developer-demo";
  useEffect(() => saveSourceDatePreference(sourceRange), [sourceRange]);
  const [countryMessage, setCountryMessage] =
    useState<TranslationKey>("loadingCountries");
  const [scenariosMessage, setScenariosMessage] =
    useState<TranslationKey>("loadingScenarios");
  const [point, setPoint] = useState<Position | null>(null);
  const pointLookup = useRef<AbortController | null>(null);
  const [mapPointMessage, setMapPointMessage] = useState<TranslationKey | null>(
    null,
  );
  useEffect(() => () => pointLookup.current?.abort(), []);
  const [saturnNotices, setSaturnNotices] = useState<SaturnNotice[]>([]);
  const [analysisRequest, setAnalysisRequest] =
    useState<AreaAnalysisRequest | null>(null);
  const investigation = useInvestigation();
  const regions =
    regionCatalog.country === country ? regionCatalog.regions : [];
  const referenceMessage: TranslationKey =
    regionCatalog.country === country
      ? regionCatalog.message
      : "loadingRegions";
  const referenceNavigation = useTerritoryReference(country, regions);
  const areaDraft = useAreaDraft(country, referenceNavigation.regionId);
  const districtBoundary = useAreaDistrictBoundary(areaDraft.preview);
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
        const savedCountry = readTerritoryPreference()?.country;
        setCountry(
          response.data.find((item) => item.code === savedCountry)?.code ??
            response.data.find((item) => item.code === PREFERRED_COUNTRY)
              ?.code ??
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
    setRegionCatalog({ country, regions: [], message: "loadingRegions" });
    if (!country) return () => controller.abort();
    void listRegions(country, controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (response.kind === "ok") {
        if (
          response.data.some(
            (item) => item.country !== country || item.kind !== "region",
          )
        ) {
          setRegionCatalog({ country, regions: [], message: "regionsFailure" });
          return;
        }
        setRegionCatalog({
          country,
          regions: response.data,
          message:
            response.data.length === 0 ? "emptyRegions" : "availableRegions",
        });
      } else {
        setRegionCatalog({
          country,
          regions: [],
          message:
            response.status === 503 ? "unavailableRegions" : "regionsFailure",
        });
      }
    });
    return () => controller.abort();
  }, [country, regionRequestVersion]);

  useEffect(() => {
    const controller = new AbortController();
    setScenarios([]);
    setTerritory("");
    setScenarioId("");
    setSeasonStart("");
    setSeasonEnd("");
    setScenariosMessage("loadingScenarios");
    if (!country || !showDeveloperDemo) return () => controller.abort();
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
  }, [country, showDeveloperDemo]);

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
    pointLookup.current?.abort();
    setMapPointMessage(null);
    setAnalysisRequest(null);
    setAnalysisAttempted(false);
    setAnalysisBusy(false);
    if (!countries.some((item) => item.code === value)) return;
    reset();
    setPoint(null);
    setSaturnNotices([]);
    saveTerritoryPreference({ country: value, regionId: "", districtId: "" });
    setRegionCatalog({
      country: value,
      regions: [],
      message: "loadingRegions",
    });
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
  const selectedBoundary = referenceNavigation.geometry?.geometry ?? null;
  const pointWithinBoundary = !!(
    point &&
    selectedBoundary &&
    isInsideArea(point, selectedBoundary)
  );
  const weatherPoint =
    areaDraft.draft?.center ??
    (pointWithinBoundary && point
      ? point
      : selectedBoundary
        ? representativePoint(selectedBoundary)
        : null);
  const canAnalyze = !!(
    country &&
    referenceNavigation.regionId &&
    referenceNavigation.districtId &&
    validSourceDateRange(sourceRange.start, sourceRange.end)
  );
  const analysisHint: TranslationKey = !referenceNavigation.regionId
    ? "analysisSelectRegion"
    : !referenceNavigation.districtId
      ? "analysisSelectDistrict"
      : !validSourceDateRange(sourceRange.start, sourceRange.end)
        ? "analysisInvalidDateRange"
        : "analysisReady";
  const analyze = () => {
    setAnalysisAttempted(true);
    if (
      !canAnalyze ||
      !referenceNavigation.regionId ||
      !referenceNavigation.districtId
    )
      return;
    setAnalysisBusy(true);
    setWeatherRefresh((value) => value + 1);
    setAnalysisRequest({
      sequence: (analysisRequest?.sequence ?? 0) + 1,
      country,
      regionId: referenceNavigation.regionId,
      districtId: referenceNavigation.districtId,
      dateStart: sourceRange.start,
      dateEnd: sourceRange.end,
    });
  };
  const chooseRegion = (id: string) => {
    pointLookup.current?.abort();
    setMapPointMessage(null);
    reset();
    setAnalysisRequest(null);
    setAnalysisAttempted(false);
    setAnalysisBusy(false);
    setSaturnNotices([]);
    setPoint(null);
    referenceNavigation.selectRegion(id);
  };
  const chooseDistrict = (id: string) => {
    pointLookup.current?.abort();
    setMapPointMessage(null);
    reset();
    setAnalysisRequest(null);
    setAnalysisAttempted(false);
    setAnalysisBusy(false);
    setSaturnNotices([]);
    setPoint(null);
    referenceNavigation.selectDistrict(id);
  };
  const selectMapPoint = (position: Position) => {
    if (areaDraft.editing) {
      void areaDraft.selectPoint(position);
      return;
    }
    pointLookup.current?.abort();
    setPoint(position);
    setMapPointMessage(null);
    setAnalysisRequest(null);
    setSaturnNotices([]);
    if (!country || regions.length === 0) return;
    const controller = new AbortController();
    pointLookup.current = controller;
    void resolveTerritoryPoint(country, position, controller.signal).then(
      (result) => {
        if (controller.signal.aborted) return;
        if (result.kind === "error") {
          setMapPointMessage(
            result.status === 404 ? "mapPointOutside" : "mapPointUnavailable",
          );
          return;
        }
        if (!regions.some((item) => item.id === result.data.region_id)) {
          setMapPointMessage("mapPointUnavailable");
          return;
        }
        reset();
        referenceNavigation.selectByPoint(
          result.data.region_id,
          result.data.district_id,
        );
      },
    );
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
      <WorkspaceHeader
        locale={locale}
        countries={countries}
        country={country}
        countryMessage={countryMessage}
        onCountry={chooseCountry}
        onLocale={setLocale}
      />
      <PlaceSearchToolbar
        country={country}
        locale={locale}
        regions={regions}
        navigation={{
          ...referenceNavigation,
          selectRegion: chooseRegion,
          selectDistrict: chooseDistrict,
        }}
        catalogMessage={referenceMessage}
        onRetryRegions={() => setRegionRequestVersion((version) => version + 1)}
        coordinateStatus={areaDraft.coordinateStatus}
        onCoordinatesEdited={areaDraft.invalidateCoordinates}
        onCoordinates={(lat, lon) => {
          void areaDraft.selectCoordinates(lat, lon).then((selection) => {
            if (
              selection?.districtId &&
              selection.regionId === referenceNavigation.regionId
            ) {
              referenceNavigation.selectByPoint(
                selection.regionId,
                selection.districtId,
              );
            }
          });
        }}
      />
      <div className="workspace workspace--places">
        <main className="canvas-column">
          <section className="map-section" aria-label={tr("mapLabel")}>
            <div className="section-header">
              <div>
                <span className="eyebrow">{tr("mapSpace")}</span>
                <h2>{tr("mapHeading")}</h2>
              </div>
            </div>
            <div className="map-point-panel" role="note">
              <div className="map-point-copy">
                <strong>{tr("startingPoint")}</strong>
                <span>
                  {point
                    ? tr("pointSelected", {
                        lat: point.latitude.toFixed(3),
                        lon: point.longitude.toFixed(3),
                      })
                    : tr("pointHelp")}
                </span>
              </div>
              {point && (
                <button
                  type="button"
                  onClick={() => {
                    pointLookup.current?.abort();
                    setPoint(null);
                    setMapPointMessage(null);
                  }}
                >
                  {tr("clear")}
                </button>
              )}
            </div>
            <MapPanel
              locale={locale}
              stops={stops}
              selectedId={investigation.selectedSite}
              startingPoint={point}
              draftPoint={areaDraft.draft?.center ?? null}
              draftBounds={areaDraft.bounds}
              privateFocus={areaDraft.coordinateFocus}
              referenceGeometry={referenceNavigation.geometry}
              previewDistrictGeometry={districtBoundary.geometry}
              saturnNotices={saturnNotices}
              onSelect={investigation.setSelectedSite}
              onPoint={selectMapPoint}
              onDraftResize={areaDraft.resize}
            />
          </section>
          <section
            className="saved-places-panel"
            aria-label={tr("workspaceSavedPlaces")}
          >
            <div className="section-header">
              <h2>{tr("workspaceSavedPlaces")}</h2>
              <span className="workspace-pending-label">
                {tr("workspaceNotAvailable")}
              </span>
            </div>
            <p className="field-help" role="status">
              {tr("workspacePlacesPending")}
            </p>
          </section>
          {mapPointMessage && (
            <p role="status" className="field-help">
              {tr(mapPointMessage)}
            </p>
          )}
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
            </div>
          )}
          {investigation.result && (
            <Timeline
              locale={locale}
              stops={stops}
              seasonStart={investigation.result.request.season_start}
              seasonEnd={investigation.result.request.season_end}
              selectedId={investigation.selectedSite}
              onSelect={investigation.setSelectedSite}
            />
          )}
          {investigation.result && (
            <EvidencePanel
              locale={locale}
              result={investigation.result}
              selectedId={investigation.selectedSite}
            />
          )}
        </main>
        <aside
          className="context-column"
          aria-label={tr("workspaceContextPanel")}
        >
          <AreaDraftPanel
            locale={locale}
            regionSelected={Boolean(referenceNavigation.regionId)}
            editing={areaDraft.editing}
            mapCoordinateStatus={areaDraft.mapCoordinateStatus}
            draft={areaDraft.draft}
            preview={areaDraft.preview}
            boundaryDistrictId={districtBoundary.districtId}
            boundaryStatus={districtBoundary.status}
            boundaryErrorCode={districtBoundary.errorCode}
            onDistrictBoundary={(id) => void districtBoundary.select(id)}
            status={areaDraft.status}
            errorCode={areaDraft.errorCode}
            onStart={areaDraft.start}
            onCancel={areaDraft.cancel}
            onWidth={(width) => areaDraft.resize("widthKm", width)}
            onHeight={(height) => areaDraft.resize("heightKm", height)}
            onCheck={() => void areaDraft.checkDistricts()}
          />
          <InvestigationControls
            locale={locale}
            scenarios={scenarios}
            territory={territory}
            scenarioId={scenarioId}
            seasonStart={seasonStart}
            seasonEnd={seasonEnd}
            selectedScenario={selectedScenario}
            busy={investigation.busy}
            canSubmit={canSubmit}
            scenariosMessage={scenariosMessage}
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
            onSubmit={begin}
            showDemo={showDeveloperDemo}
            canAnalyze={canAnalyze}
            onAnalyze={analyze}
            analysisBusy={analysisBusy}
            analysisAttempted={analysisAttempted}
            sourceDateStart={sourceRange.start}
            sourceDateEnd={sourceRange.end}
            onSourceDateStart={(value) => {
              setSourceRange((current) =>
                updateSourceDateRange(current, "start", value),
              );
              setAnalysisRequest(null);
              setAnalysisAttempted(false);
              setAnalysisBusy(false);
              setSaturnNotices([]);
            }}
            onSourceDateEnd={(value) => {
              setSourceRange((current) =>
                updateSourceDateRange(current, "end", value),
              );
              setAnalysisRequest(null);
              setAnalysisAttempted(false);
              setAnalysisBusy(false);
              setSaturnNotices([]);
            }}
            analysisHint={analysisHint}
          />
          <WeatherPanel
            country={country}
            locale={locale}
            point={weatherPoint}
            refreshToken={weatherRefresh}
          />
          <LiveAreaAnalysis
            locale={locale}
            country={country}
            regionId={referenceNavigation.regionId}
            request={analysisRequest}
            onNotices={setSaturnNotices}
            onBusy={setAnalysisBusy}
          />
        </aside>
      </div>
      <footer className="footer-note">{tr("footer")}</footer>
    </div>
  );
}
