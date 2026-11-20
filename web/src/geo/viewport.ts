/** Only the browser-local map camera is retained, never a selected apiary point. */
export interface MapViewport {
  latitude: number;
  longitude: number;
  zoom: number;
}

export const VIEWPORT_STORAGE_KEY = "melliatlas.map.viewport.v1";
export const DEFAULT_VIEWPORT: MapViewport = {
  latitude: 55,
  longitude: 42,
  zoom: 4,
};

// Inverse spherical Web Mercator at projected y = pi is atan(sinh(pi))°.
// This is the projection domain limit (about 85.05113°), not a user setting.
const MAX_MERCATOR_LATITUDE = 85.05112878;
// Browser payload-size cap: the camera consists of exactly three numeric fields.
const MAX_STORED_VIEWPORT_CHARS = 160;
// Camera zoom limits are chosen for the supported OpenStreetMap tile layer.
const MIN_MAP_ZOOM = 2;
export const MAX_MAP_ZOOM = 18;
const WGS84_MAX_LONGITUDE = 180;
// Reduce local-storage precision; do not treat a map camera as a surveyed point.
const STORED_COORDINATE_DECIMALS = 4;

/** Reject malformed or out-of-range persisted camera data before passing it to Leaflet. */
export function parseMapViewport(raw: string | null): MapViewport | null {
  if (!raw || raw.length > MAX_STORED_VIEWPORT_CHARS) return null;
  try {
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed))
      return null;
    if (
      !("latitude" in parsed) ||
      !("longitude" in parsed) ||
      !("zoom" in parsed)
    )
      return null;
    const { latitude, longitude, zoom } = parsed;
    if (
      typeof latitude !== "number" ||
      typeof longitude !== "number" ||
      typeof zoom !== "number" ||
      !Number.isFinite(latitude) ||
      !Number.isFinite(longitude) ||
      !Number.isInteger(zoom) ||
      Math.abs(latitude) > MAX_MERCATOR_LATITUDE ||
      Math.abs(longitude) > WGS84_MAX_LONGITUDE ||
      zoom < MIN_MAP_ZOOM ||
      zoom > MAX_MAP_ZOOM
    )
      return null;
    return { latitude, longitude, zoom };
  } catch {
    return null;
  }
}

/** Remove a previously saved camera when a point may represent a private location. */
export function clearMapViewport(): void {
  try {
    window.localStorage.removeItem(VIEWPORT_STORAGE_KEY);
  } catch {
    // Storage restrictions must not affect map selection.
  }
}

/** Storage can be disabled by the browser; map usage must still work. */
export function readMapViewport(): MapViewport | null {
  try {
    return parseMapViewport(window.localStorage.getItem(VIEWPORT_STORAGE_KEY));
  } catch {
    return null;
  }
}

export function saveMapViewport(viewport: MapViewport): void {
  try {
    window.localStorage.setItem(
      VIEWPORT_STORAGE_KEY,
      JSON.stringify({
        latitude: Number(viewport.latitude.toFixed(STORED_COORDINATE_DECIMALS)),
        longitude: Number(
          viewport.longitude.toFixed(STORED_COORDINATE_DECIMALS),
        ),
        zoom: viewport.zoom,
      }),
    );
  } catch {
    // Private browsing and storage restrictions must not disable map interaction.
  }
}
