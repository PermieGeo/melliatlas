import { useEffect, useRef, useState } from "react";
import {
  listExternalSources,
  readSaturnPage,
  readWeatherForecast,
} from "../api/client";
import type {
  CountryCode,
  ExternalSource,
  Position,
  SaturnNotice,
  SaturnNoticePage,
  WeatherForecast,
} from "../api/types";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

/** An explicit user action, scoped to one geographic selection and its weather point. */
export interface AreaAnalysisRequest {
  sequence: number;
  country: CountryCode;
  regionId: string;
  point: Position;
}

interface Props {
  country: CountryCode;
  regionId: string;
  locale: Locale;
  request: AreaAnalysisRequest | null;
  onNotices: (notices: SaturnNotice[]) => void;
}

type ReadResult<T> = { kind: "ok"; data: T } | { kind: "error"; code: string };
interface Report {
  request: AreaAnalysisRequest;
  saturn: ReadResult<SaturnNoticePage> | null;
  weather: ReadResult<WeatherForecast> | null;
}

/** Never treat missing upstream data as evidence that treatments or risks are absent. */
export function LiveAreaAnalysis({
  country,
  regionId,
  locale,
  request,
  onNotices,
}: Props) {
  const [sources, setSources] = useState<ExternalSource[]>([]);
  const [sourceError, setSourceError] = useState(false);
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [morePages, setMorePages] = useState<{
    sequence: number;
    country: CountryCode;
    regionId: string;
    pages: SaturnNoticePage[];
  } | null>(null);
  const [pagingBusy, setPagingBusy] = useState(false);
  const [pagingError, setPagingError] = useState<string | null>(null);
  const pagingController = useRef<AbortController | null>(null);
  useEffect(
    () => () => pagingController.current?.abort(),
    [country, regionId, request],
  );
  const noticesRef = useRef(onNotices);
  noticesRef.current = onNotices;
  const tr = (key: TranslationKey, values?: Record<string, string | number>) =>
    t(locale, key, values);

  useEffect(() => {
    const controller = new AbortController();
    setSources([]);
    setSourceError(false);
    if (country) {
      void listExternalSources(country, controller.signal).then((response) => {
        if (controller.signal.aborted) return;
        if (response.kind === "error") {
          setSourceError(true);
          return;
        }
        setSources(
          response.data.filter((source) => source.country === country),
        );
      });
    }
    return () => controller.abort();
  }, [country]);

  useEffect(() => {
    const controller = new AbortController();
    setReport(null);
    setMorePages(null);
    setPagingError(null);
    setPagingBusy(false);
    setBusy(false);
    noticesRef.current([]);
    if (
      !request ||
      request.country !== country ||
      request.regionId !== regionId
    ) {
      return () => controller.abort();
    }
    const hasSaturn =
      country === "RU" && sources.some((source) => source.id === "saturn");
    const hasWeather = sources.some((source) => source.id === "open-meteo");
    if (!hasSaturn && !hasWeather) return () => controller.abort();
    setBusy(true);
    void Promise.all([
      hasSaturn
        ? readSaturnPage(country, regionId, 0, controller.signal)
        : Promise.resolve(null),
      hasWeather
        ? readWeatherForecast(request.point, controller.signal)
        : Promise.resolve(null),
    ]).then(([saturn, weather]) => {
      if (controller.signal.aborted) return;
      const checkedSaturn: ReadResult<SaturnNoticePage> | null =
        saturn?.kind === "ok"
          ? saturn.data.country === country &&
            saturn.data.region_id === regionId
            ? { kind: "ok", data: saturn.data }
            : { kind: "error", code: "INVALID_RESPONSE" }
          : saturn?.kind === "error"
            ? { kind: "error", code: saturn.code }
            : null;
      const checkedWeather: ReadResult<WeatherForecast> | null =
        weather?.kind === "ok"
          ? weather.data.requested_latitude === request.point.latitude &&
            weather.data.requested_longitude === request.point.longitude
            ? { kind: "ok", data: weather.data }
            : { kind: "error", code: "INVALID_RESPONSE" }
          : weather?.kind === "error"
            ? { kind: "error", code: weather.code }
            : null;
      setReport({ request, saturn: checkedSaturn, weather: checkedWeather });
      setBusy(false);
      noticesRef.current(
        checkedSaturn?.kind === "ok" ? checkedSaturn.data.notices : [],
      );
    });
    return () => controller.abort();
  }, [country, regionId, request, sources]);

  const shown =
    report?.request.country === country &&
    report.request.regionId === regionId &&
    report.request.sequence === request?.sequence
      ? report
      : null;
  const extraPages =
    morePages?.sequence === request?.sequence &&
    morePages?.country === country &&
    morePages?.regionId === regionId
      ? morePages.pages
      : [];
  const forecast = shown?.weather?.kind === "ok" ? shown.weather.data : null;
  const page = shown?.saturn?.kind === "ok" ? shown.saturn.data : null;
  const pages = page ? [page, ...extraPages] : [];
  const uniqueNotices = [
    ...new Map(
      pages
        .flatMap((entry) => entry.notices)
        .map((notice) => [notice.record_id, notice] as const),
    ).values(),
  ];
  const lastPage = pages[pages.length - 1] ?? null;
  const geometryCount = uniqueNotices.filter(
    (notice) => notice.geometry !== null,
  ).length;
  const loadNextPage = () => {
    if (
      !page ||
      !lastPage ||
      lastPage.next_page === null ||
      pagingBusy ||
      !request
    )
      return;
    const nextNumber = lastPage.next_page;
    const controller = new AbortController();
    pagingController.current?.abort();
    pagingController.current = controller;
    setPagingBusy(true);
    setPagingError(null);
    void readSaturnPage(country, regionId, nextNumber, controller.signal).then(
      (response) => {
        if (controller.signal.aborted) return;
        setPagingBusy(false);
        if (response.kind === "error") {
          setPagingError(response.code);
          return;
        }
        if (
          response.data.country !== country ||
          response.data.region_id !== regionId ||
          response.data.page_number !== nextNumber ||
          response.data.total_elements !== page.total_elements ||
          response.data.source_id !== page.source_id ||
          (response.data.next_page !== null &&
            response.data.next_page <= nextNumber)
        ) {
          setPagingError("INVALID_RESPONSE");
          return;
        }
        const loaded = [...extraPages, response.data];
        setMorePages({
          sequence: request.sequence,
          country,
          regionId,
          pages: loaded,
        });
        const merged = [
          ...new Map(
            [page, ...loaded]
              .flatMap((entry) => entry.notices)
              .map((notice) => [notice.record_id, notice] as const),
          ).values(),
        ];
        noticesRef.current(merged);
      },
    );
  };
  return (
    <section className="live-analysis" aria-label={tr("analysisResultsTitle")}>
      <h2>{tr("analysisResultsTitle")}</h2>
      {sourceError && <p role="alert">{tr("analysisSourcesUnavailable")}</p>}
      {busy && <p role="status">{tr("analysisWorking")}</p>}
      {!request && <p className="field-help">{tr("analysisAwaiting")}</p>}
      {request && !busy && !shown && sources.length === 0 && !sourceError && (
        <p className="field-help">{tr("analysisNoProviders")}</p>
      )}
      {shown && (
        <div role="status" className="analysis-findings">
          <p className="warning-text">{tr("analysisPartialDisclaimer")}</p>
          {shown.saturn?.kind === "error" && (
            <p role="alert">
              {shown.saturn.code === "SOURCE_REGION_UNMAPPED"
                ? tr("analysisSaturnRegionUnmapped")
                : tr("saturnError", { reason: shown.saturn.code })}
            </p>
          )}
          {page && (
            <div className="analysis-source-result">
              <h3>{tr("saturnTitle")}</h3>
              <p>
                {tr("analysisSaturnPageProgress", {
                  pages: pages.length,
                  records: uniqueNotices.length,
                  total: page.total_elements ?? tr("saturnMissing"),
                })}
              </p>
              <p className="field-help">
                {tr("analysisSaturnGeometryCount", { count: geometryCount })}
              </p>
              {geometryCount === 0 && (
                <p className="field-help">{tr("analysisSaturnNoGeometry")}</p>
              )}
              <p className="field-help">
                {tr("analysisSaturnPartial", {
                  total: page.total_elements ?? tr("saturnMissing"),
                })}
              </p>
              {uniqueNotices.slice(0, 20).map((notice) => (
                <details key={notice.record_id} className="saturn-record">
                  <summary>
                    {tr("saturnField", {
                      record: notice.record_id,
                      plan: notice.plan_id ?? tr("saturnMissing"),
                    })}
                  </summary>
                  <p>
                    {tr("saturnDates", {
                      start: notice.scheduled_start ?? tr("saturnMissing"),
                      end: notice.scheduled_end ?? tr("saturnMissing"),
                    })}
                  </p>
                  {notice.products.map((product, index) => (
                    <p key={index}>
                      {tr("saturnProduct", {
                        name: product.name ?? tr("saturnMissing"),
                        crop: product.crop ?? tr("saturnMissing"),
                        hazard:
                          product.reported_bee_hazard_class ??
                          tr("saturnMissing"),
                      })}
                    </p>
                  ))}
                </details>
              ))}
              {uniqueNotices.length > 20 && (
                <p className="field-help">
                  {tr("analysisSaturnCount", {
                    count: uniqueNotices.length,
                    skipped: pages.reduce(
                      (sum, entry) => sum + entry.unidentified_records,
                      0,
                    ),
                  })}
                </p>
              )}
              {pagingError && (
                <p role="alert">{tr("saturnError", { reason: pagingError })}</p>
              )}
              {lastPage?.next_page !== null &&
                lastPage?.next_page !== undefined && (
                  <button
                    type="button"
                    disabled={pagingBusy}
                    onClick={loadNextPage}
                  >
                    {tr(
                      pagingBusy
                        ? "analysisSaturnLoadingNext"
                        : "analysisSaturnLoadNext",
                    )}
                  </button>
                )}
            </div>
          )}
          {shown.weather?.kind === "error" && (
            <p role="alert">
              {tr("weatherError", { reason: shown.weather.code })}
            </p>
          )}
          {forecast && (
            <div className="analysis-source-result">
              <h3>{tr("weatherTitle")}</h3>
              <p className="field-help">{tr("weatherWarning")}</p>
              <details>
                <summary>
                  {tr("analysisForecastHours", {
                    count: forecast.hours.length,
                  })}
                </summary>
                <div className="weather-scroll">
                  <table className="weather-table">
                    <thead>
                      <tr>
                        <th>{tr("weatherTime")}</th>
                        <th>{tr("weatherWind")}</th>
                        <th>{tr("weatherDirection")}</th>
                        <th>{tr("weatherGusts")}</th>
                        <th>{tr("weatherRain")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecast.hours.map((hour) => (
                        <tr key={hour.time}>
                          <td>{hour.time.slice(0, 16).replace("T", " ")}</td>
                          {[
                            hour.wind_speed_kmh,
                            hour.wind_direction_degrees,
                            hour.wind_gusts_kmh,
                            hour.precipitation_mm,
                          ].map((value, i) => (
                            <td key={i}>
                              {value === null ? tr("weatherMissing") : value}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
              <a
                href={forecast.source_uri}
                target="_blank"
                rel="noopener noreferrer"
              >
                {tr("weatherAttribution")}
              </a>
            </div>
          )}
          {shown.saturn === null && (
            <p className="field-help">{tr("analysisSaturnNotSupported")}</p>
          )}
          {shown.weather === null && (
            <p className="field-help">{tr("analysisWeatherNotEnabled")}</p>
          )}
        </div>
      )}
    </section>
  );
}
