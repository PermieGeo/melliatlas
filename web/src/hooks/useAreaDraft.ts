import { useEffect, useMemo, useRef, useState } from "react";
import { lookupIntersectingDistricts } from "../api/client";
import type { AreaDistrictResult, CountryCode, Position } from "../api/types";
import {
  DEFAULT_DRAFT_DIMENSION_KM,
  provisionalDraftRectangle,
  validDraftDimension,
} from "../geo/analysisDraft";

export interface AnalysisDraft {
  country: CountryCode;
  regionId: string;
  center: Position;
  widthKm: number;
  heightKm: number;
}

interface DistrictPreview {
  draft: AnalysisDraft;
  result: AreaDistrictResult;
}

type LookupStatus = "idle" | "loading" | "ready" | "failed";

/** Keep private analysis coordinates in React memory, never browser storage or URLs. */
export function useAreaDraft(country: CountryCode, regionId: string) {
  const [editing, setEditing] = useState(false);
  const [storedDraft, setStoredDraft] = useState<AnalysisDraft | null>(null);
  const [preview, setPreview] = useState<DistrictPreview | null>(null);
  const [status, setStatus] = useState<LookupStatus>("idle");
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const inFlight = useRef<AbortController | null>(null);
  const revision = useRef(0);
  const draft =
    storedDraft?.country === country && storedDraft.regionId === regionId
      ? storedDraft
      : null;
  const bounds = useMemo(
    () =>
      draft
        ? provisionalDraftRectangle(draft.center, draft.widthKm, draft.heightKm)
        : null,
    [draft],
  );
  const currentPreview = preview?.draft === draft ? preview.result : null;

  const invalidate = () => {
    revision.current += 1;
    inFlight.current?.abort();
    inFlight.current = null;
    setPreview(null);
    setStatus("idle");
    setErrorCode(null);
  };

  useEffect(() => {
    revision.current += 1;
    inFlight.current?.abort();
    inFlight.current = null;
    setEditing(false);
    setStoredDraft(null);
    setPreview(null);
    setStatus("idle");
    setErrorCode(null);
    return () => {
      revision.current += 1;
      inFlight.current?.abort();
    };
  }, [country, regionId]);

  const start = () => {
    if (!country || !regionId) return;
    invalidate();
    setStoredDraft(null);
    setEditing(true);
  };
  const cancel = () => {
    invalidate();
    setStoredDraft(null);
    setEditing(false);
  };
  const selectPoint = (center: Position) => {
    if (!editing || !country || !regionId) return false;
    const rectangle = provisionalDraftRectangle(
      center,
      DEFAULT_DRAFT_DIMENSION_KM,
      DEFAULT_DRAFT_DIMENSION_KM,
    );
    if (rectangle === null) return false;
    invalidate();
    setStoredDraft({
      country,
      regionId,
      center,
      widthKm: DEFAULT_DRAFT_DIMENSION_KM,
      heightKm: DEFAULT_DRAFT_DIMENSION_KM,
    });
    return true;
  };
  const resize = (axis: "widthKm" | "heightKm", value: number) => {
    if (!draft || !validDraftDimension(value)) return;
    const next = { ...draft, [axis]: value };
    if (!provisionalDraftRectangle(next.center, next.widthKm, next.heightKm))
      return;
    invalidate();
    setStoredDraft(next);
  };
  const checkDistricts = async () => {
    if (!draft || !bounds || status === "loading") return;
    invalidate();
    const controller = new AbortController();
    inFlight.current = controller;
    const token = revision.current;
    setStatus("loading");
    const response = await lookupIntersectingDistricts(
      draft,
      controller.signal,
    );
    if (controller.signal.aborted || revision.current !== token) return;
    inFlight.current = null;
    if (response.kind === "error") {
      setStatus("failed");
      setErrorCode(response.code);
      return;
    }
    setPreview({ draft, result: response.data });
    setStatus("ready");
  };
  return {
    editing,
    draft,
    bounds,
    preview: currentPreview,
    status,
    errorCode,
    start,
    cancel,
    selectPoint,
    resize,
    checkDistricts,
  };
}
