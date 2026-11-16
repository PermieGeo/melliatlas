/** Only public administrative IDs are persisted; never persist chosen apiary coordinates. */
export interface TerritoryPreference {
  country: string;
  regionId: string;
  districtId: string;
}

export const TERRITORY_PREFERENCE_KEY = "melliatlas.territory.selection.v1";
const MAX_PREFERENCE_CHARS = 400;
const COUNTRY_CODE = /^[A-Z]{2}$/;
const TERRITORY_ID = /^[a-z]{2}:(?:region|district):[a-z0-9-]{1,128}$/;

/** Parse defensively: a removed country or district is revalidated against live catalogs. */
export function parseTerritoryPreference(
  raw: string | null,
): TerritoryPreference | null {
  if (!raw || raw.length > MAX_PREFERENCE_CHARS) return null;
  try {
    const value: unknown = JSON.parse(raw);
    if (typeof value !== "object" || value === null || Array.isArray(value))
      return null;
    if (
      !("country" in value) ||
      !("regionId" in value) ||
      !("districtId" in value)
    )
      return null;
    if (
      Object.keys(value).some(
        (key) => !["country", "regionId", "districtId"].includes(key),
      )
    )
      return null;
    const { country, regionId, districtId } = value;
    if (
      typeof country !== "string" ||
      !COUNTRY_CODE.test(country) ||
      typeof regionId !== "string" ||
      typeof districtId !== "string" ||
      (regionId !== "" &&
        (!TERRITORY_ID.test(regionId) ||
          !regionId.startsWith(`${country.toLowerCase()}:region:`))) ||
      (districtId !== "" &&
        (regionId === "" ||
          !TERRITORY_ID.test(districtId) ||
          !districtId.startsWith(`${country.toLowerCase()}:district:`)))
    )
      return null;
    return { country, regionId, districtId };
  } catch {
    return null;
  }
}

export function readTerritoryPreference(): TerritoryPreference | null {
  try {
    return parseTerritoryPreference(
      window.localStorage.getItem(TERRITORY_PREFERENCE_KEY),
    );
  } catch {
    return null;
  }
}

export function saveTerritoryPreference(preference: TerritoryPreference): void {
  if (!parseTerritoryPreference(JSON.stringify(preference))) return;
  try {
    window.localStorage.setItem(
      TERRITORY_PREFERENCE_KEY,
      JSON.stringify(preference),
    );
  } catch {
    // Storage denial must not interrupt public geography selection.
  }
}
