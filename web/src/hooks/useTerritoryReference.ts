import { useEffect, useState } from "react";
import { getTerritoryGeometry, listDistricts } from "../api/client";
import type { CountryCode, Territory, TerritoryGeometry } from "../api/types";
import type { TranslationKey } from "../i18n";

/** Reference navigation is independent of fictional scenario territories and study results. */
export interface TerritoryNavigation {
  regionId: string;
  districts: Territory[];
  districtId: string;
  districtMessage: TranslationKey;
  geometryMessage: TranslationKey;
  geometry: TerritoryGeometry | null;
  selectRegion: (id: string) => void;
  selectDistrict: (id: string) => void;
}

/** Own cancellable country-scoped district and geometry reads, without caching private positions. */
export function useTerritoryReference(
  country: CountryCode,
  regions: Territory[],
): TerritoryNavigation {
  const [regionId, setRegionId] = useState("");
  const [districtId, setDistrictId] = useState("");
  const [districts, setDistricts] = useState<Territory[]>([]);
  const [districtMessage, setDistrictMessage] = useState<TranslationKey>(
    "referenceSelectRegion",
  );
  const [geometryMessage, setGeometryMessage] = useState<TranslationKey>(
    "referenceSelectRegion",
  );
  const [loadedGeometry, setLoadedGeometry] =
    useState<TerritoryGeometry | null>(null);

  const region = regions.find(
    (item) =>
      item.id === regionId &&
      item.country === country &&
      item.kind === "region",
  );
  const district = districts.find(
    (item) => item.id === districtId && item.parent_id === region?.id,
  );
  const selected = district ?? region;
  const regionIdForRequest = region?.id ?? "";
  const territoryIdForRequest = selected?.id ?? "";
  const referenceIdForRequest = selected?.reference_id ?? "";
  const geometryStatusForRequest = selected?.geometry_status ?? null;

  useEffect(() => {
    const controller = new AbortController();
    setDistrictId("");
    setDistricts([]);
    setDistrictMessage(
      regionIdForRequest ? "referenceDistrictLoading" : "referenceSelectRegion",
    );
    if (!regionIdForRequest) return () => controller.abort();
    void listDistricts(regionIdForRequest, controller.signal).then(
      (response) => {
        if (controller.signal.aborted) return;
        if (response.kind === "error") {
          setDistrictMessage(
            response.status === 409
              ? "referenceDistrictUnsupported"
              : "referenceDistrictUnavailable",
          );
          return;
        }
        if (
          response.data.some(
            (item) =>
              item.country !== country ||
              item.parent_id !== regionIdForRequest ||
              item.kind !== "district",
          )
        ) {
          setDistrictMessage("referenceDistrictUnavailable");
          return;
        }
        setDistricts(response.data);
        setDistrictMessage(
          response.data.length
            ? "referenceDistrictAvailable"
            : "referenceDistrictEmpty",
        );
      },
    );
    return () => controller.abort();
  }, [country, regionIdForRequest]);

  useEffect(() => {
    const controller = new AbortController();
    setLoadedGeometry(null);
    if (!territoryIdForRequest) {
      setGeometryMessage("referenceSelectRegion");
      return () => controller.abort();
    }
    if (geometryStatusForRequest !== "available") {
      setGeometryMessage(
        geometryStatusForRequest === "missing"
          ? "referenceGeometryMissing"
          : "referenceGeometryInvalid",
      );
      return () => controller.abort();
    }
    setGeometryMessage("referenceGeometryLoading");
    void getTerritoryGeometry(territoryIdForRequest, controller.signal).then(
      (response) => {
        if (controller.signal.aborted) return;
        if (response.kind === "error") {
          setGeometryMessage(
            response.status === 404
              ? "referenceGeometryMissing"
              : "referenceGeometryUnavailable",
          );
          return;
        }
        if (
          response.data.territory_id !== territoryIdForRequest ||
          response.data.reference_id !== referenceIdForRequest
        ) {
          setGeometryMessage("referenceGeometryUnavailable");
          return;
        }
        setLoadedGeometry(response.data);
        setGeometryMessage("referenceGeometryAvailable");
      },
    );
    return () => controller.abort();
  }, [territoryIdForRequest, referenceIdForRequest, geometryStatusForRequest]);

  return {
    regionId: region?.id ?? "",
    districts: region ? districts : [],
    districtId: district?.id ?? "",
    districtMessage,
    geometryMessage,
    geometry:
      loadedGeometry &&
      selected &&
      loadedGeometry.territory_id === selected.id &&
      loadedGeometry.reference_id === selected.reference_id
        ? loadedGeometry
        : null,
    selectRegion: (id) => {
      setRegionId(id);
      setDistrictId("");
    },
    selectDistrict: (id) => {
      if (
        districts.some(
          (item) => item.id === id && item.parent_id === region?.id,
        )
      )
        setDistrictId(id);
      else setDistrictId("");
    },
  };
}
