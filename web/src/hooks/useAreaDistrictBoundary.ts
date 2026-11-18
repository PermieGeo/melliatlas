import { useEffect, useRef, useState } from "react";
import { getTerritoryGeometry } from "../api/client";
import type { AreaDistrictResult, TerritoryGeometry } from "../api/types";

type BoundaryStatus = "idle" | "loading" | "ready" | "failed";

interface BoundarySelection {
  preview: AreaDistrictResult;
  districtId: string;
  status: BoundaryStatus;
  geometry: TerritoryGeometry | null;
  errorCode: string | null;
}

/** Inspect one publicly available ADM2 boundary without fetching every overlapping district. */
export function useAreaDistrictBoundary(preview: AreaDistrictResult | null) {
  const request = useRef<AbortController | null>(null);
  const revision = useRef(0);
  const [selection, setSelection] = useState<BoundarySelection | null>(null);
  const active = selection?.preview === preview ? selection : null;

  const clear = () => {
    revision.current += 1;
    request.current?.abort();
    request.current = null;
    setSelection(null);
  };

  useEffect(() => {
    revision.current += 1;
    request.current?.abort();
    request.current = null;
    setSelection(null);
    return () => {
      revision.current += 1;
      request.current?.abort();
    };
  }, [preview]);

  const select = async (districtId: string) => {
    if (!preview) return;
    const district = preview.districts.find((item) => item.id === districtId);
    if (!district) return;
    if (active?.districtId === districtId) {
      clear();
      return;
    }
    clear();
    const controller = new AbortController();
    request.current = controller;
    const token = revision.current;
    setSelection({
      preview,
      districtId,
      status: "loading",
      geometry: null,
      errorCode: null,
    });
    const result = await getTerritoryGeometry(district.id, controller.signal);
    if (controller.signal.aborted || revision.current !== token) return;
    request.current = null;
    if (result.kind === "error") {
      setSelection({
        preview,
        districtId,
        status: "failed",
        geometry: null,
        errorCode: result.code,
      });
      return;
    }
    if (
      result.data.territory_id !== district.id ||
      result.data.reference_id !== district.reference_id
    ) {
      setSelection({
        preview,
        districtId,
        status: "failed",
        geometry: null,
        errorCode: "INVALID_RESPONSE",
      });
      return;
    }
    setSelection({
      preview,
      districtId,
      status: "ready",
      geometry: result.data,
      errorCode: null,
    });
  };

  return {
    districtId: active?.districtId ?? null,
    status: active?.status ?? "idle",
    geometry: active?.geometry ?? null,
    errorCode: active?.errorCode ?? null,
    select,
    clear,
  };
}
