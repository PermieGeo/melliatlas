import { useEffect, useRef, useState } from "react";
import { listExternalSources, readSaturnPage } from "../api/client";
import { SATURN_PAGE_COUNT, SATURN_RECORD_LIMIT } from "../api/types";
import type { DraftRectangle } from "../geo/analysisDraft";
import { scopeSaturnNotices } from "../geo/saturnFootprint";
import type {
  CountryCode,
  ExternalSource,
  SaturnNotice,
  SaturnNoticePage,
} from "../api/types";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

/** One explicit district-scoped Saturn read; weather loads separately above the map. */
export interface AreaAnalysisRequest {
  sequence: number;
  country: CountryCode;
  regionId: string;
  districtId: string;
  dateStart: string;
  dateEnd: string;
  area: DraftRectangle | null;
}

interface Props {
  country: CountryCode;
  regionId: string;
  locale: Locale;
  request: AreaAnalysisRequest | null;
  onNotices: (notices: SaturnNotice[]) => void;
  onBusy?: (busy: boolean) => void;
}

type ReadResult<T> = { kind: "ok"; data: T } | { kind: "error"; code: string };
interface Report {
  request: AreaAnalysisRequest;
  saturn: ReadResult<SaturnNoticePage> | null;
}

/** Never treat missing upstream data as evidence that treatments or risks are absent. */

export function LiveAreaAnalysis({
  country,
  regionId,
  locale,
  request,
  onNotices,
  onBusy,
}: Props) {
  const [sources, setSources] = useState<ExternalSource[]>([]);
  const [sourceError, setSourceError] = useState(false);
  const [sourceRetry, setSourceRetry] = useState(0);
  const [sourceLoading, setSourceLoading] = useState(true);
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
  const busyRef = useRef(onBusy);
  busyRef.current = onBusy;
  useEffect(() => {
    busyRef.current?.(busy);
  }, [busy, request]);
  const noticesRef = useRef(onNotices);
  noticesRef.current = onNotices;
  const tr = (key: TranslationKey, values?: Record<string, string | number>) =>
    t(locale, key, values);

  useEffect(() => {
    const controller = new AbortController();
    setSources([]);
    setSourceError(false);
    setSourceLoading(true);
    if (country) {
      void listExternalSources(country, controller.signal).then((response) => {
        if (controller.signal.aborted) return;
        setSourceLoading(false);
        if (response.kind === "error") {
          setSourceError(true);
          return;
        }
        setSources(
          response.data.filter((source) => source.country === country),
        );
      });
    } else {
      setSourceLoading(false);
    }
    return () => controller.abort();
  }, [country, sourceRetry]);

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
    if (sourceLoading) {
      setBusy(true);
      return () => controller.abort();
    }
    const hasSaturn =
      country === "RU" && sources.some((source) => source.id === "saturn");
    if (!hasSaturn) {
      setReport({ request, saturn: null });
      return () => controller.abort();
    }
    setBusy(true);
    void readSaturnPage(country, regionId, 0, controller.signal, {
      districtId: request.districtId,
      dateStart: request.dateStart,
      dateEnd: request.dateEnd,
    }).then((saturn) => {
      if (controller.signal.aborted) return;
      const checkedSaturn: ReadResult<SaturnNoticePage> | null =
        saturn?.kind === "ok"
          ? saturn.data.country === country &&
            saturn.data.region_id === regionId &&
            saturn.data.district_id === request.districtId &&
            saturn.data.date_start === request.dateStart &&
            saturn.data.date_end === request.dateEnd
            ? { kind: "ok", data: saturn.data }
            : { kind: "error", code: "INVALID_RESPONSE" }
          : saturn?.kind === "error"
            ? { kind: "error", code: saturn.code }
            : null;
      setReport({ request, saturn: checkedSaturn });
      setBusy(false);
      noticesRef.current(
        checkedSaturn?.kind === "ok"
          ? scopeSaturnNotices(checkedSaturn.data.notices, request.area).matched
          : [],
      );
    });
    return () => controller.abort();
  }, [country, regionId, request, sources, sourceLoading]);

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
  const hasSaturn =
    country === "RU" && sources.some((source) => source.id === "saturn");
  const page = shown?.saturn?.kind === "ok" ? shown.saturn.data : null;
  const pages = page ? [page, ...extraPages] : [];
  const uniqueNotices = [
    ...new Map(
      pages
        .flatMap((entry) => entry.notices)
        .map((notice) => [notice.record_id, notice] as const),
    ).values(),
  ];
  const scoped = scopeSaturnNotices(uniqueNotices, request?.area ?? null);
  const visibleNotices = scoped.matched;
  const lastPage = pages[pages.length - 1] ?? null;
  const recordLimitExceeded = pages.some(
    (entry) => entry.record_limit_exceeded,
  );
  const geometryCount = uniqueNotices.filter(
    (notice) => notice.geometry !== null,
  ).length;
  const loadNextPage = () => {
    if (
      !page ||
      !lastPage ||
      lastPage.next_page === null ||
      lastPage.next_page >= SATURN_PAGE_COUNT ||
      pages.length >= SATURN_PAGE_COUNT ||
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
    void readSaturnPage(country, regionId, nextNumber, controller.signal, {
      districtId: request.districtId,
      dateStart: request.dateStart,
      dateEnd: request.dateEnd,
    }).then((response) => {
      if (controller.signal.aborted) return;
      setPagingBusy(false);
      if (response.kind === "error") {
        setPagingError(response.code);
        return;
      }
      if (
        response.data.country !== country ||
        response.data.region_id !== regionId ||
        response.data.district_id !== request.districtId ||
        response.data.date_start !== request.dateStart ||
        response.data.date_end !== request.dateEnd ||
        response.data.page_number !== nextNumber ||
        response.data.total_elements !== page.total_elements ||
        response.data.source_id !== page.source_id ||
        response.data.page_number >= SATURN_PAGE_COUNT ||
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
      noticesRef.current(scopeSaturnNotices(merged, request.area).matched);
    });
  };
  return (
    <section className="live-analysis" aria-label={tr("analysisResultsTitle")}>
      <h2>{tr("analysisResultsTitle")}</h2>
      {sourceError && (
        <div className="source-feedback source-feedback--warning">
          <p role="alert">{tr("analysisSourcesUnavailable")}</p>
          <button
            type="button"
            className="source-retry"
            onClick={() => setSourceRetry((value) => value + 1)}
          >
            {tr("sourceRetry")}
          </button>
        </div>
      )}
      {(sourceLoading || busy) && (
        <p role="status" className="source-feedback source-feedback--loading">
          <span className="analysis-spinner" aria-hidden="true" />
          {tr(sourceLoading ? "analysisCheckingSources" : "analysisWorking")}
        </p>
      )}
      {!sourceLoading && !sourceError && !hasSaturn && (
        <div className="source-feedback source-feedback--warning" role="status">
          <p>{tr("analysisSaturnNotSupported")}</p>
          <p className="field-help">{tr("analysisSaturnEnableHelp")}</p>
          <button
            type="button"
            className="source-retry"
            onClick={() => setSourceRetry((value) => value + 1)}
          >
            {tr("sourceRetry")}
          </button>
        </div>
      )}
      {!request && !sourceLoading && !sourceError && hasSaturn && (
        <p role="status" className="source-feedback source-feedback--ready">
          {tr("analysisSaturnReady")}
        </p>
      )}
      {!request && <p className="field-help">{tr("analysisAwaiting")}</p>}
      {shown && (
        <div role="status" className="analysis-findings">
          <p className="warning-text">{tr("analysisPartialDisclaimer")}</p>
          {shown.saturn?.kind === "error" && (
            <p
              role="alert"
              className="source-feedback source-feedback--warning"
            >
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
              {recordLimitExceeded && (
                <p role="alert" className="analysis-empty">
                  {tr("analysisSaturnRecordLimit", {
                    limit: SATURN_RECORD_LIMIT,
                  })}
                </p>
              )}
              {visibleNotices.length === 0 && (
                <div className="analysis-empty" role="status">
                  <strong>
                    {tr(
                      request?.area && uniqueNotices.length > 0
                        ? "analysisNoDraftMatchesTitle"
                        : "analysisNoRecordsTitle",
                    )}
                  </strong>
                  <p>
                    {tr(
                      request?.area && uniqueNotices.length > 0
                        ? "analysisNoDraftMatchesDetail"
                        : "analysisNoRecordsDetail",
                    )}
                  </p>
                </div>
              )}
              <p className="field-help">
                {request?.area
                  ? tr("analysisSaturnWithinDraft", {
                      matched: visibleNotices.length,
                      outside: scoped.outside,
                      unlocated: scoped.unlocated,
                    })
                  : tr("analysisSaturnDistrictOnly")}
              </p>
              <p className="field-help">
                {tr("analysisSaturnGeometryCount", { count: geometryCount })}
              </p>
              {uniqueNotices.length > 0 && geometryCount === 0 && (
                <p className="field-help">{tr("analysisSaturnNoGeometry")}</p>
              )}
              <p className="field-help">
                {tr("analysisSaturnPartial", {
                  total: page.total_elements ?? tr("saturnMissing"),
                })}
              </p>
              {visibleNotices.slice(0, SATURN_RECORD_LIMIT).map((notice) => (
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
              {visibleNotices.length > SATURN_RECORD_LIMIT && (
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
              {pagingBusy && (
                <p
                  role="status"
                  className="source-feedback source-feedback--loading"
                >
                  <span className="analysis-spinner" aria-hidden="true" />
                  {tr("analysisSaturnLoadingNext")}
                </p>
              )}
              {pagingError && (
                <p
                  role="alert"
                  className="source-feedback source-feedback--warning"
                >
                  {tr("saturnError", { reason: pagingError })}
                </p>
              )}
              {lastPage?.next_page !== null &&
                lastPage?.next_page !== undefined &&
                lastPage.next_page < SATURN_PAGE_COUNT &&
                pages.length < SATURN_PAGE_COUNT && (
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
          {shown.saturn === null && (
            <p className="field-help">{tr("analysisSaturnNotSupported")}</p>
          )}
        </div>
      )}
    </section>
  );
}
