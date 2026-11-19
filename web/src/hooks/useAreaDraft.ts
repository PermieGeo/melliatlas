import { useEffect, useMemo, useRef, useState } from "react";
import {
  lookupIntersectingDistricts,
  resolveTerritoryPoint,
} from "../api/client";
import type { AreaDistrictResult, CountryCode, Position } from "../api/types";
import {
  DEFAULT_DRAFT_DIMENSION_KM,
  parseDraftCoordinates,
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
type CoordinateStatus =
  "idle" | "checking" | "invalid" | "outside" | "unavailable";
type VerifiedCenter = { regionId: string; districtId: string | null };

/** Keep private analysis coordinates in React memory, never browser storage or URLs. */
export function useAreaDraft(country: CountryCode, regionId: string) {
  const scope = `${country}:${regionId}`;
  const activeScope = useRef(scope);
  activeScope.current = scope;
  const [editing, setEditing] = useState(false);
  const [storedDraft, setStoredDraft] = useState<AnalysisDraft | null>(null);
  const [preview, setPreview] = useState<DistrictPreview | null>(null);
  const [status, setStatus] = useState<LookupStatus>("idle");
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const inFlight = useRef<AbortController | null>(null);
  const revision = useRef(0);
  const coordinateRequest = useRef<AbortController | null>(null);
  const coordinateVersion = useRef(0);
  const [coordinateStatus, setCoordinateStatus] =
    useState<CoordinateStatus>("idle");
  const [coordinateFocus, setCoordinateFocus] = useState<Position | null>(null);
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

  const invalidateCoordinates = () => {
    coordinateVersion.current += 1;
    coordinateRequest.current?.abort();
    coordinateRequest.current = null;
    setCoordinateStatus("idle");
  };

  const invalidate = () => {
    invalidateCoordinates();
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
    coordinateVersion.current += 1;
    coordinateRequest.current?.abort();
    coordinateRequest.current = null;
    setCoordinateStatus("idle");
    setCoordinateFocus(null);
    setEditing(false);
    setStoredDraft(null);
    setPreview(null);
    setStatus("idle");
    setErrorCode(null);
    return () => {
      revision.current += 1;
      inFlight.current?.abort();
      coordinateVersion.current += 1;
      coordinateRequest.current?.abort();
    };
  }, [country, regionId]);

  const start = () => {
    if (!country || !regionId) return;
    invalidate();
    setStoredDraft(null);
    setCoordinateFocus(null);
    setEditing(true);
  };
  const cancel = () => {
    invalidate();
    setStoredDraft(null);
    setCoordinateFocus(null);
    setEditing(false);
  };
  const applyCenter = (center: Position, focus: boolean) => {
    if (!country || !regionId) return false;
    const widthKm = draft?.widthKm ?? DEFAULT_DRAFT_DIMENSION_KM;
    const heightKm = draft?.heightKm ?? DEFAULT_DRAFT_DIMENSION_KM;
    if (!provisionalDraftRectangle(center, widthKm, heightKm)) return false;
    invalidate();
    setStoredDraft({ country, regionId, center, widthKm, heightKm });
    setCoordinateFocus(focus ? center : null);
    return true;
  };
  // Map clicks and typed coordinates require the same authoritative region check.
  const verifyCenter = async (
    center: Position | null,
    focus: boolean,
  ): Promise<VerifiedCenter | null> => {
    if (!country || !regionId) return null;
    invalidateCoordinates();
    const widthKm = draft?.widthKm ?? DEFAULT_DRAFT_DIMENSION_KM;
    const heightKm = draft?.heightKm ?? DEFAULT_DRAFT_DIMENSION_KM;
    if (!center || !provisionalDraftRectangle(center, widthKm, heightKm)) {
      setCoordinateStatus("invalid");
      return null;
    }
    const controller = new AbortController();
    coordinateRequest.current = controller;
    const token = coordinateVersion.current;
    const requestScope = scope;
    setCoordinateStatus("checking");
    const response = await resolveTerritoryPoint(
      country,
      center,
      controller.signal,
    );
    if (
      controller.signal.aborted ||
      coordinateVersion.current !== token ||
      activeScope.current !== requestScope
    )
      return null;
    coordinateRequest.current = null;
    if (response.kind === "error") {
      setCoordinateStatus(response.status === 404 ? "outside" : "unavailable");
      return null;
    }
    if (response.data.region_id !== regionId) {
      setCoordinateStatus("outside");
      return null;
    }
    if (applyCenter(center, focus)) {
      setEditing(true);
      return { regionId, districtId: response.data.district_id };
    }
    return null;
  };
  const selectPoint = (center: Position): Promise<VerifiedCenter | null> =>
    editing ? verifyCenter(center, false) : Promise.resolve(null);
  const selectCoordinates = (
    latitude: string,
    longitude: string,
  ): Promise<VerifiedCenter | null> =>
    verifyCenter(parseDraftCoordinates(latitude, longitude), true);
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
    coordinateStatus,
    coordinateFocus,
    invalidateCoordinates,
    selectCoordinates,
    start,
    cancel,
    selectPoint,
    resize,
    checkDistricts,
  };
}
