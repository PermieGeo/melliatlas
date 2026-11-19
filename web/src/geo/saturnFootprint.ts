import type { GeoPosition, ReferenceShape, SaturnNotice } from "../api/types";
import type { DraftRectangle } from "./analysisDraft";

type Rectangle = { west: number; east: number; south: number; north: number };

function unwrapRing(ring: GeoPosition[], anchor: number): GeoPosition[] {
  let previous = anchor;
  return ring.map(([longitude, latitude]) => {
    const adjusted = longitude + 360 * Math.round((previous - longitude) / 360);
    previous = adjusted;
    return [adjusted, latitude];
  });
}

function isInsideRectangle([x, y]: GeoPosition, box: Rectangle): boolean {
  return x >= box.west && x <= box.east && y >= box.south && y <= box.north;
}

function segmentTouchesRectangle(
  [ax, ay]: GeoPosition,
  [bx, by]: GeoPosition,
  box: Rectangle,
): boolean {
  const dx = bx - ax;
  const dy = by - ay;
  let enter = 0;
  let leave = 1;
  const edges: ReadonlyArray<readonly [number, number]> = [
    [-dx, ax - box.west],
    [dx, box.east - ax],
    [-dy, ay - box.south],
    [dy, box.north - ay],
  ];
  for (const [p, q] of edges) {
    if (p === 0) {
      if (q < 0) return false;
      continue;
    }
    const ratio = q / p;
    if (p < 0) enter = Math.max(enter, ratio);
    else leave = Math.min(leave, ratio);
    if (enter > leave) return false;
  }
  return true;
}

function pointInRing([x, y]: GeoPosition, ring: GeoPosition[]): boolean {
  let inside = false;
  for (
    let index = 0, previous = ring.length - 1;
    index < ring.length;
    previous = index++
  ) {
    const a = ring[index];
    const b = ring[previous];
    if (!a || !b) continue;
    if (
      a[1] > y !== b[1] > y &&
      x < ((b[0] - a[0]) * (y - a[1])) / (b[1] - a[1]) + a[0]
    ) {
      inside = !inside;
    }
  }
  return inside;
}

function polygonTouchesRectangle(
  rings: GeoPosition[][],
  box: Rectangle,
): boolean {
  const outer = rings[0];
  if (!outer?.length) return false;
  let minLongitude = Infinity;
  let maxLongitude = -Infinity;
  for (const [longitude] of outer) {
    minLongitude = Math.min(minLongitude, longitude);
    maxLongitude = Math.max(maxLongitude, longitude);
  }
  const center = (minLongitude + maxLongitude) / 2;
  const boxCenter = (box.west + box.east) / 2;
  const approximateShift = Math.round((center - boxCenter) / 360);
  for (const shift of [
    approximateShift - 1,
    approximateShift,
    approximateShift + 1,
  ]) {
    const shifted = {
      ...box,
      west: box.west + 360 * shift,
      east: box.east + 360 * shift,
    };
    for (const ring of rings) {
      for (let index = 0; index < ring.length; index++) {
        const a = ring[index];
        const b = ring[(index + 1) % ring.length];
        if (!a || !b) continue;
        if (
          isInsideRectangle(a, shifted) ||
          segmentTouchesRectangle(a, b, shifted)
        ) {
          return true;
        }
      }
    }
    const corners: GeoPosition[] = [
      [shifted.west, shifted.south],
      [shifted.west, shifted.north],
      [shifted.east, shifted.south],
      [shifted.east, shifted.north],
    ];
    if (
      corners.some(
        (corner) =>
          pointInRing(corner, outer) &&
          !rings.slice(1).some((hole) => pointInRing(corner, hole)),
      )
    ) {
      return true;
    }
  }
  return false;
}

/** A reported field must intersect the draft, not merely share its district. */
export function saturnGeometryTouchesDraft(
  geometry: ReferenceShape,
  draft: DraftRectangle,
): boolean {
  const polygons =
    geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
  return polygons.some((polygon) => {
    const first = polygon[0]?.[0];
    if (!first) return false;
    const outer = unwrapRing(polygon[0] ?? [], first[0]);
    const rings = [
      outer,
      ...polygon
        .slice(1)
        .map((hole) => unwrapRing(hole, outer[0]?.[0] ?? first[0])),
    ];
    return draft.longitudeRanges.some(([west, east]) =>
      polygonTouchesRectangle(rings, {
        west,
        east,
        south: draft.south,
        north: draft.north,
      }),
    );
  });
}

export function scopeSaturnNotices(
  notices: SaturnNotice[],
  draft: DraftRectangle | null,
): { matched: SaturnNotice[]; unlocated: number; outside: number } {
  if (!draft) return { matched: notices, unlocated: 0, outside: 0 };
  const matched: SaturnNotice[] = [];
  let unlocated = 0;
  let outside = 0;
  for (const notice of notices) {
    if (!notice.geometry) unlocated++;
    else if (saturnGeometryTouchesDraft(notice.geometry, draft))
      matched.push(notice);
    else outside++;
  }
  return { matched, unlocated, outside };
}
