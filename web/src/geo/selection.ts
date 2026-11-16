import type { Position, ReferenceShape } from "../api/types";

/** Bounding-box dimensions are a UI guard, not an exposure or source coverage model. */
export interface AreaSize {
  center: Position;
  widthKm: number;
  heightKm: number;
}

/** Calculate a display center and approximate size from validated WGS84 geometry. */
export function areaSize(shape: ReferenceShape): AreaSize | null {
  let minLon = Infinity;
  let maxLon = -Infinity;
  let minLat = Infinity;
  let maxLat = -Infinity;
  const polygons =
    shape.type === "Polygon" ? [shape.coordinates] : shape.coordinates;
  for (const polygon of polygons)
    for (const ring of polygon)
      for (const position of ring) {
        minLon = Math.min(minLon, position[0]);
        maxLon = Math.max(maxLon, position[0]);
        minLat = Math.min(minLat, position[1]);
        maxLat = Math.max(maxLat, position[1]);
      }
  if (![minLon, maxLon, minLat, maxLat].every(Number.isFinite)) return null;
  const midLat = (minLat + maxLat) / 2;
  return {
    center: { longitude: (minLon + maxLon) / 2, latitude: midLat },
    widthKm: (maxLon - minLon) * 111.32 * Math.cos((midLat * Math.PI) / 180),
    heightKm: (maxLat - minLat) * 111.32,
  };
}

function insideRing(point: Position, ring: [number, number][]): boolean {
  let inside = false;
  for (
    let index = 0, previous = ring.length - 1;
    index < ring.length;
    previous = index++
  ) {
    const current = ring[index];
    const last = ring[previous];
    if (!current || !last) continue;
    const [x, y] = current;
    const [px, py] = last;
    if (
      y > point.latitude !== py > point.latitude &&
      point.longitude < ((px - x) * (point.latitude - y)) / (py - y) + x
    )
      inside = !inside;
  }
  return inside;
}

/** A selected point must be inside the territory; bounding-box containment is insufficient. */
export function isInsideArea(point: Position, shape: ReferenceShape): boolean {
  const polygons =
    shape.type === "Polygon" ? [shape.coordinates] : shape.coordinates;
  return polygons.some((polygon) => {
    const outer = polygon[0];
    return (
      outer !== undefined &&
      insideRing(point, outer) &&
      !polygon.slice(1).some((hole) => insideRing(point, hole))
    );
  });
}
