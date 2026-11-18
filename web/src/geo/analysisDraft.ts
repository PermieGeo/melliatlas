import type { Position } from "../api/types";

export const DEFAULT_DRAFT_DIMENSION_KM = 15;
export const MAX_DRAFT_DIMENSION_KM = 30;

const WGS84_EQUATORIAL_RADIUS_METERS = 6_378_137;
const WGS84_ECCENTRICITY_SQUARED = 6.6943799901413165e-3;

export interface DraftRectangle {
  south: number;
  north: number;
  longitudeRanges: [number, number][];
}

/** Draw only a provisional rectangle. Server PostGIS geometry remains authoritative. */
export function provisionalDraftRectangle(
  center: Position,
  widthKm: number,
  heightKm: number,
): DraftRectangle | null {
  if (
    !Number.isFinite(center.latitude) ||
    !Number.isFinite(center.longitude) ||
    Math.abs(center.latitude) > 90 ||
    Math.abs(center.longitude) > 180 ||
    !validDraftDimension(widthKm) ||
    !validDraftDimension(heightKm)
  )
    return null;
  const latitudeRadians = (center.latitude * Math.PI) / 180;
  const sinLatitude = Math.sin(latitudeRadians);
  const scale = 1 - WGS84_ECCENTRICITY_SQUARED * sinLatitude ** 2;
  const meridionalRadius =
    (WGS84_EQUATORIAL_RADIUS_METERS * (1 - WGS84_ECCENTRICITY_SQUARED)) /
    scale ** 1.5;
  const primeVerticalRadius = WGS84_EQUATORIAL_RADIUS_METERS / Math.sqrt(scale);
  const kmPerDegreeLatitude = (Math.PI * meridionalRadius) / 180_000;
  const kmPerDegreeLongitude =
    (Math.PI * primeVerticalRadius * Math.cos(latitudeRadians)) / 180_000;
  if (kmPerDegreeLongitude <= 0) return null;
  const latitudeDelta = heightKm / (2 * kmPerDegreeLatitude);
  const longitudeDelta = widthKm / (2 * kmPerDegreeLongitude);
  if (
    center.latitude - latitudeDelta <= -90 ||
    center.latitude + latitudeDelta >= 90 ||
    longitudeDelta >= 180
  )
    return null;
  const west = center.longitude - longitudeDelta;
  const east = center.longitude + longitudeDelta;
  const longitudeRanges: [number, number][] =
    east > 180
      ? [
          [west, 180],
          [-180, east - 360],
        ]
      : west < -180
        ? [
            [west + 360, 180],
            [-180, east],
          ]
        : [[west, east]];
  return {
    south: center.latitude - latitudeDelta,
    north: center.latitude + latitudeDelta,
    longitudeRanges,
  };
}

export function validDraftDimension(value: number): boolean {
  return Number.isFinite(value) && value > 0 && value <= MAX_DRAFT_DIMENSION_KM;
}

/** Parse one latitude and one longitude field without accepting implicit numeric coercion. */
export function parseDraftCoordinates(
  latitudeText: string,
  longitudeText: string,
): Position | null {
  const parse = (value: string): number | null => {
    const trimmed = value.trim();
    if (!/^[+-]?[0-9]+(?:[.,][0-9]+)?$/.test(trimmed)) return null;
    const number = Number(trimmed.replace(",", "."));
    return Number.isFinite(number) ? number : null;
  };
  const latitude = parse(latitudeText);
  const longitude = parse(longitudeText);
  if (
    latitude === null ||
    longitude === null ||
    Math.abs(latitude) > 90 ||
    Math.abs(longitude) > 180
  )
    return null;
  return { latitude, longitude };
}
