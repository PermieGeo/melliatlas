import { useEffect, useRef, useState } from "react";
import { listExternalSources, readSaturnPage } from "../api/client";
import { SATURN_PAGE_COUNT, SATURN_RECORD_LIMIT } from "../api/types";
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
      noticesRef.current(merged);
    });
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
              {recordLimitExceeded && (
                <p role="alert" className="analysis-empty">
                  {tr("analysisSaturnRecordLimit", {
                    limit: SATURN_RECORD_LIMIT,
                  })}
                </p>
              )}
              {uniqueNotices.length === 0 && (
                <div className="analysis-empty" role="status">
                  <strong>{tr("analysisNoRecordsTitle")}</strong>
                  <p>{tr("analysisNoRecordsDetail")}</p>
                </div>
              )}
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
              {uniqueNotices.slice(0, SATURN_RECORD_LIMIT).map((notice) => (
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
              {uniqueNotices.length > SATURN_RECORD_LIMIT && (
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
