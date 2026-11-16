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
  selectByPoint: (regionId: string, districtId: string | null) => void;
  retryDistricts: () => void;
}

/** Own cancellable country-scoped district and geometry reads, without caching private positions. */
export function useTerritoryReference(
  country: CountryCode,
  regions: Territory[],
): TerritoryNavigation {
  const [regionSelection, setRegionSelection] = useState<{
    country: CountryCode;
    regionId: string;
  }>({ country: "", regionId: "" });
  const regionId =
    regionSelection.country === country ? regionSelection.regionId : "";

  useEffect(() => {
    setRegionSelection({ country, regionId: "" });
  }, [country]);
  const [districtId, setDistrictId] = useState("");
  const [pendingPointDistrict, setPendingPointDistrict] = useState<{
    country: CountryCode;
    regionId: string;
    districtId: string;
  } | null>(null);
  const [districtRequestVersion, setDistrictRequestVersion] = useState(0);
  const [districtResult, setDistrictResult] = useState<{
    regionId: string;
    districts: Territory[];
    message: TranslationKey;
  }>({ regionId: "", districts: [], message: "referenceSelectRegion" });
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
  const regionIdForRequest = region?.id ?? "";
  const districts =
    districtResult.regionId === regionIdForRequest
      ? districtResult.districts
      : [];
  const districtMessage: TranslationKey = !regionIdForRequest
    ? "referenceSelectRegion"
    : districtResult.regionId === regionIdForRequest
      ? districtResult.message
      : "referenceDistrictLoading";
  const district = districts.find(
    (item) => item.id === districtId && item.parent_id === regionIdForRequest,
  );
  const selected = district ?? region;
  const territoryIdForRequest = selected?.id ?? "";
  const referenceIdForRequest = selected?.reference_id ?? "";
  const geometryStatusForRequest = selected?.geometry_status ?? null;

  useEffect(() => {
    const controller = new AbortController();
    setDistrictId("");
    setDistrictResult({
      regionId: regionIdForRequest,
      districts: [],
      message: regionIdForRequest
        ? "referenceDistrictLoading"
        : "referenceSelectRegion",
    });
    if (!regionIdForRequest) return () => controller.abort();
    void listDistricts(regionIdForRequest, controller.signal).then(
      (response) => {
        if (controller.signal.aborted) return;
        if (response.kind === "error") {
          setDistrictResult({
            regionId: regionIdForRequest,
            districts: [],
            message:
              response.status === 409
                ? "referenceDistrictUnsupported"
                : "referenceDistrictUnavailable",
          });
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
          setDistrictResult({
            regionId: regionIdForRequest,
            districts: [],
            message: "referenceDistrictUnavailable",
          });
          return;
        }
        setDistrictResult({
          regionId: regionIdForRequest,
          districts: response.data,
          message: response.data.length
            ? "referenceDistrictAvailable"
            : "referenceDistrictEmpty",
        });
      },
    );
    return () => controller.abort();
  }, [country, regionIdForRequest, districtRequestVersion]);

  useEffect(() => {
    if (
      !pendingPointDistrict ||
      pendingPointDistrict.country !== country ||
      pendingPointDistrict.regionId !== regionIdForRequest ||
      districtResult.regionId !== regionIdForRequest ||
      districtResult.message === "referenceDistrictLoading"
    )
      return;
    setDistrictId(
      districts.some((item) => item.id === pendingPointDistrict.districtId)
        ? pendingPointDistrict.districtId
        : "",
    );
    setPendingPointDistrict(null);
  }, [
    country,
    regionIdForRequest,
    districtResult,
    districts,
    pendingPointDistrict,
  ]);

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
      setPendingPointDistrict(null);
      setRegionSelection({ country, regionId: id });
      setDistrictId("");
    },
    selectByPoint: (newRegionId, newDistrictId) => {
      if (
        !regions.some(
          (item) => item.id === newRegionId && item.country === country,
        )
      )
        return;
      setRegionSelection({ country, regionId: newRegionId });
      setDistrictId("");
      setPendingPointDistrict(
        newDistrictId
          ? {
              country,
              regionId: newRegionId,
              districtId: newDistrictId,
            }
          : null,
      );
    },
    retryDistricts: () => {
      if (regionIdForRequest)
        setDistrictRequestVersion((version) => version + 1);
    },
    selectDistrict: (id) => {
      setPendingPointDistrict(null);
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
