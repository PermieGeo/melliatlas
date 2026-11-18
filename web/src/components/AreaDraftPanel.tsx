import { useEffect, useState } from "react";
import type { AreaDistrictResult } from "../api/types";
import type { AnalysisDraft } from "../hooks/useAreaDraft";
import type { Locale } from "../i18n";
import { t } from "../i18n";

interface Props {
  locale: Locale;
  regionSelected: boolean;
  editing: boolean;
  draft: AnalysisDraft | null;
  status: "idle" | "loading" | "ready" | "failed";
  errorCode: string | null;
  coordinateStatus: "idle" | "checking" | "invalid" | "outside" | "unavailable";
  preview: AreaDistrictResult | null;
  onStart: () => void;
  onCoordinatesEdited: () => void;
  onCoordinates: (latitude: string, longitude: string) => void;
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
  draft,
  status,
  errorCode,
  preview,
  coordinateStatus,
  onStart,
  onCoordinatesEdited,
  onCoordinates,
  onCancel,
  onWidth,
  onHeight,
  onCheck,
}: Props) {
  const tr = (key: Parameters<typeof t>[1]) => t(locale, key);
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const centerLatitude = draft?.center.latitude;
  const centerLongitude = draft?.center.longitude;
  useEffect(() => {
    setLatitude(centerLatitude === undefined ? "" : String(centerLatitude));
    setLongitude(centerLongitude === undefined ? "" : String(centerLongitude));
  }, [centerLatitude, centerLongitude]);
  return (
    <section className="area-draft-panel" aria-label={tr("draftAreaTitle")}>
      <div className="area-draft-header">
        <h3>{tr("draftAreaTitle")}</h3>
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
      <p className="field-help">
        {!regionSelected
          ? tr("draftAreaNeedsRegion")
          : editing
            ? tr("draftAreaClickHint")
            : tr("draftAreaIntro")}
      </p>
      {editing && (
        <form
          className="area-draft-coordinates"
          onSubmit={(event) => {
            event.preventDefault();
            onCoordinates(latitude, longitude);
          }}
        >
          <label>
            {tr("draftAreaLatitude")}
            <input
              aria-label={tr("draftAreaLatitude")}
              inputMode="decimal"
              autoComplete="off"
              value={latitude}
              onChange={(event) => {
                setLatitude(event.target.value);
                onCoordinatesEdited();
              }}
            />
          </label>
          <label>
            {tr("draftAreaLongitude")}
            <input
              aria-label={tr("draftAreaLongitude")}
              inputMode="decimal"
              autoComplete="off"
              value={longitude}
              onChange={(event) => {
                setLongitude(event.target.value);
                onCoordinatesEdited();
              }}
            />
          </label>
          <button type="submit" disabled={coordinateStatus === "checking"}>
            {coordinateStatus === "checking"
              ? tr("draftAreaVerifying")
              : tr("draftAreaApplyCoordinates")}
          </button>
          {coordinateStatus !== "idle" && coordinateStatus !== "checking" && (
            <p role="status" className="field-help">
              {tr(
                coordinateStatus === "invalid"
                  ? "draftAreaCoordinateInvalid"
                  : coordinateStatus === "outside"
                    ? "draftAreaCoordinateOutside"
                    : "draftAreaCoordinateUnavailable",
              )}
            </p>
          )}
        </form>
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
        <div role="status" className="area-draft-results">
          <p>
            {t(locale, "draftAreaDistricts", {
              count: preview.districts.length,
            })}
          </p>
          <p className="field-help">
            {preview.coverage === "MISSING"
              ? tr("draftAreaMissing")
              : tr("draftAreaUnverified")}
          </p>
          <ul>
            {preview.districts.map((district) => (
              <li key={district.id}>{district.name}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="field-help">{tr("draftAreaUnsaved")}</p>
    </section>
  );
}
