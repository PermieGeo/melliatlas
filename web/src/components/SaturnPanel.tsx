import { useEffect, useRef, useState } from "react";
import { listExternalSources, readSaturnPage } from "../api/client";
import type { CountryCode, SaturnNotice, SaturnNoticePage } from "../api/types";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

/** No Saturn country assumptions: server-declared capabilities govern visibility. */
interface Props {
  country: CountryCode;
  locale: Locale;
  regionId: string;
  onNotices: (notices: SaturnNotice[]) => void;
}

/** Isolated public notice reader. It never mutates synthetic investigations. */
export function SaturnPanel({ country, locale, regionId, onNotices }: Props) {
  const [availableCountry, setAvailableCountry] = useState("");
  const [result, setResult] = useState<{
    country: string;
    regionId: string;
    page: SaturnNoticePage;
  } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const fetchController = useRef<AbortController | null>(null);
  const onNoticesRef = useRef(onNotices);
  onNoticesRef.current = onNotices;
  const tr = (key: TranslationKey, values?: Record<string, string | number>) =>
    t(locale, key, values);

  useEffect(() => {
    const controller = new AbortController();
    fetchController.current?.abort();
    onNoticesRef.current([]);
    setBusy(false);
    setError("");
    setResult(null);
    setAvailableCountry("");
    void listExternalSources(country, controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      setAvailableCountry(
        response.kind === "ok" &&
          response.data.some(
            (source) => source.id === "saturn" && source.country === country,
          )
          ? country
          : "",
      );
    });
    return () => {
      controller.abort();
      fetchController.current?.abort();
    };
  }, [country]);

  useEffect(() => {
    fetchController.current?.abort();
    onNoticesRef.current([]);
    setBusy(false);
    setError("");
    setResult(null);
  }, [regionId]);

  const validRegion =
    country === "RU" && /^ru:region:[a-z0-9-]+$/.test(regionId);
  const visible = availableCountry === country && country !== "";
  const shown =
    result?.country === country && result.regionId === regionId
      ? result.page
      : null;
  const nextPage = shown?.next_page ?? null;

  const read = (pageNumber: number) => {
    if (!visible || !validRegion || busy) return;
    fetchController.current?.abort();
    const controller = new AbortController();
    fetchController.current = controller;
    setBusy(true);
    setError("");
    setResult(null);
    onNoticesRef.current([]);
    void readSaturnPage(country, regionId, pageNumber, controller.signal).then(
      (response) => {
        if (controller.signal.aborted) return;
        setBusy(false);
        if (response.kind === "error") {
          setError(response.code);
          return;
        }
        if (
          response.data.country !== country ||
          response.data.region_id !== regionId ||
          response.data.page_number !== pageNumber
        ) {
          setError("INVALID_RESPONSE");
          return;
        }
        setResult({ country, regionId, page: response.data });
        onNoticesRef.current(response.data.notices);
      },
    );
  };

  if (!visible) return null;
  return (
    <section className="saturn-panel" aria-label={tr("saturnTitle")}>
      <h2>{tr("saturnTitle")}</h2>
      <p className="warning-text">{tr("saturnWarning")}</p>
      <div className="saturn-controls">
        <button
          type="button"
          disabled={!validRegion || busy}
          onClick={() => read(0)}
        >
          {busy ? tr("saturnLoading") : tr("saturnRead")}
        </button>
      </div>
      {!validRegion && (
        <p className="field-help" role="status">
          {tr("saturnSelectRegion")}
        </p>
      )}
      {validRegion && <p className="field-help">{tr("saturnCodeHint")}</p>}
      {error && (
        <p role="alert" className="warning-text">
          {error === "SOURCE_REGION_UNMAPPED"
            ? tr("saturnUnmapped")
            : tr("saturnError", { reason: error })}
        </p>
      )}
      {shown && (
        <div role="status">
          <p>
            {tr("saturnCount", {
              page: shown.page_number + 1,
              count: shown.notices.length,
              skipped: shown.unidentified_records,
            })}
          </p>
          <p className="muted">
            {tr("saturnCaptured", {
              time: shown.captured_at,
              source: shown.source_id,
            })}
          </p>
          {shown.notices.length === 0 && (
            <p className="warning-text">{tr("saturnEmpty")}</p>
          )}
          {shown.notices.map((notice) => (
            <article
              className="saturn-record"
              key={`${notice.source_id}:${notice.record_id}`}
            >
              <strong>
                {tr("saturnField", {
                  record: notice.record_id,
                  plan: notice.plan_id ?? tr("saturnMissing"),
                })}
              </strong>
              <p>
                {tr("saturnDates", {
                  start: notice.scheduled_start ?? tr("saturnMissing"),
                  end: notice.scheduled_end ?? tr("saturnMissing"),
                })}
              </p>
              {!notice.geometry && (
                <p className="muted">{tr("saturnGeometry")}</p>
              )}
              {notice.products.map((product, index) => (
                <p key={index}>
                  {tr("saturnProduct", {
                    name: product.name ?? tr("saturnMissing"),
                    crop: product.crop ?? tr("saturnMissing"),
                    hazard:
                      product.reported_bee_hazard_class ?? tr("saturnMissing"),
                  })}
                </p>
              ))}
              {notice.uncertainties.map((note) => (
                <p className="warning-text" key={note}>
                  {note}
                </p>
              ))}
            </article>
          ))}
          <p className="warning-text">{tr("saturnMore")}</p>
          {nextPage !== null && (
            <button
              type="button"
              disabled={busy}
              onClick={() => read(nextPage)}
            >
              {tr("saturnNext")}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
