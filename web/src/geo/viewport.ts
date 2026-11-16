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

const MAX_MERCATOR_LATITUDE = 85.05112878;
const MAX_MAP_ZOOM = 18;

/** Reject malformed or out-of-range persisted camera data before passing it to Leaflet. */
export function parseMapViewport(raw: string | null): MapViewport | null {
  if (!raw || raw.length > 160) return null;
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
      Math.abs(longitude) > 180 ||
      zoom < 2 ||
      zoom > MAX_MAP_ZOOM
    )
      return null;
    return { latitude, longitude, zoom };
  } catch {
    return null;
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
        latitude: Number(viewport.latitude.toFixed(4)),
        longitude: Number(viewport.longitude.toFixed(4)),
        zoom: viewport.zoom,
      }),
    );
  } catch {
    // Private browsing and storage restrictions must not disable map interaction.
  }
}
