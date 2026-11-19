import type { AreaDistrictResult } from "../api/types";
import type { AnalysisDraft, CoordinateStatus } from "../hooks/useAreaDraft";
import type { Locale } from "../i18n";
import { t } from "../i18n";
import { FieldHelp } from "./FieldHelp";

interface Props {
  locale: Locale;
  regionSelected: boolean;
  editing: boolean;
  mapCoordinateStatus: CoordinateStatus;
  draft: AnalysisDraft | null;
  status: "idle" | "loading" | "ready" | "failed";
  errorCode: string | null;
  preview: AreaDistrictResult | null;
  boundaryDistrictId: string | null;
  boundaryStatus: "idle" | "loading" | "ready" | "failed";
  boundaryErrorCode: string | null;
  onDistrictBoundary: (districtId: string) => void;
  onStart: () => void;
  onCancel: () => void;
  onWidth: (width: number) => void;
  onHeight: (height: number) => void;
  onCheck: () => void;
}

/** Unsaved area preview: never imply that a private place was persisted. */
export function AreaDraftPanel({
  locale,
  regionSelected,
  editing,
  mapCoordinateStatus,
  draft,
  status,
  errorCode,
  preview,
  boundaryDistrictId,
  boundaryStatus,
  boundaryErrorCode,
  onDistrictBoundary,
  onStart,
  onCancel,
  onWidth,
  onHeight,
  onCheck,
}: Props) {
  const tr = (key: Parameters<typeof t>[1]) => t(locale, key);
  return (
    <section className="area-draft-panel" aria-label={tr("draftAreaTitle")}>
      <div className="area-draft-header">
        <div className="label-with-help">
          <h3>{tr("draftAreaTitle")}</h3>
          <FieldHelp
            locale={locale}
            label="draftAreaTitle"
            explanation="draftAreaClickHint"
          />
        </div>
        {editing ? (
          <button type="button" onClick={onCancel}>
            {tr("draftAreaCancel")}
          </button>
        ) : (
          <button type="button" onClick={onStart} disabled={!regionSelected}>
            {tr("draftAreaStart")}
          </button>
        )}
      </div>
      {!regionSelected && (
        <p className="field-help" role="status">
          {tr("draftAreaNeedsRegion")}
        </p>
      )}
      {editing && mapCoordinateStatus === "checking" && (
        <p className="field-help" role="status">
          {tr("draftAreaVerifying")}
        </p>
      )}
      {editing && mapCoordinateStatus === "invalid" && (
        <p className="field-help" role="status">
          {tr("draftAreaCoordinateInvalid")}
        </p>
      )}
      {editing &&
        (mapCoordinateStatus === "outside" ||
          mapCoordinateStatus === "unavailable") && (
          <p className="field-help" role="status">
            {tr(
              mapCoordinateStatus === "outside"
                ? "draftAreaCoordinateOutside"
                : "draftAreaCoordinateUnavailable",
            )}
          </p>
        )}
      {draft && (
        <>
          <div className="area-draft-dimensions">
            <label>
              {tr("draftAreaWidth")}
              <input
                aria-label={tr("draftAreaWidth")}
                type="number"
                min="0.1"
                max="30"
                step="0.1"
                value={draft.widthKm}
                onChange={(event) => onWidth(Number(event.target.value))}
              />
            </label>
            <label>
              {tr("draftAreaHeight")}
              <input
                aria-label={tr("draftAreaHeight")}
                type="number"
                min="0.1"
                max="30"
                step="0.1"
                value={draft.heightKm}
                onChange={(event) => onHeight(Number(event.target.value))}
              />
            </label>
          </div>
          <p className="field-help">
            {t(locale, "draftAreaSize", {
              area: (draft.widthKm * draft.heightKm).toFixed(2),
            })}
          </p>
          <button
            type="button"
            onClick={onCheck}
            disabled={status === "loading"}
          >
            {status === "loading"
              ? tr("draftAreaChecking")
              : tr("draftAreaCheck")}
          </button>
        </>
      )}
      {status === "failed" && (
        <p role="status" className="field-help">
          {t(locale, "draftAreaError", { code: errorCode ?? "UNKNOWN" })}
        </p>
      )}
      {preview && (
        <div className="area-draft-results">
          <p role="status">
            {t(locale, "draftAreaDistricts", {
              count: preview.districts.length,
            })}
          </p>
          <p className="field-help">
            {preview.coverage === "MISSING"
              ? tr("draftAreaMissing")
              : tr("draftAreaUnverified")}
          </p>
          <ul className="area-draft-district-list">
            {preview.districts.map((district) => (
              <li key={district.id}>
                <span>{district.name}</span>
                <button
                  type="button"
                  aria-pressed={boundaryDistrictId === district.id}
                  onClick={() => onDistrictBoundary(district.id)}
                >
                  {boundaryDistrictId === district.id
                    ? tr("draftAreaHideBoundary")
                    : tr("draftAreaShowBoundary")}
                </button>
              </li>
            ))}
          </ul>
          {boundaryStatus === "loading" && (
            <p className="field-help">{tr("draftAreaBoundaryLoading")}</p>
          )}
          {boundaryStatus === "failed" && (
            <p role="alert" className="field-help">
              {t(locale, "draftAreaBoundaryUnavailable", {
                code: boundaryErrorCode ?? "UNKNOWN",
              })}
            </p>
          )}
          {boundaryStatus === "ready" && (
            <p className="field-help">{tr("draftAreaBoundaryShown")}</p>
          )}
        </div>
      )}
      <p className="field-help">{tr("draftAreaUnsaved")}</p>
    </section>
  );
}
