import { describe, expect, it, vi } from "vitest";
import { getTerritoryGeometry } from "../src/api/client";
import { decodeTerritoryGeometry, WireError } from "../src/api/validation";

const polygon = {
  type: "Polygon",
  coordinates: [
    [
      [32, 54],
      [33, 54],
      [33, 55],
      [32, 54],
    ],
  ],
};
const response = {
  territory_id: "ru:region:reference",
  reference_id: "reference-2026",
  coordinate_system: "EPSG:4326",
  geometry: polygon,
};

describe("verified territory geometry API boundary", () => {
  it("reads WGS84 Polygon and MultiPolygon shapes", () => {
    expect(decodeTerritoryGeometry(response)).toMatchObject(response);
    expect(
      decodeTerritoryGeometry({
        ...response,
        geometry: { type: "MultiPolygon", coordinates: [polygon.coordinates] },
      }).geometry.type,
    ).toBe("MultiPolygon");
  });

  it("rejects invalid CRS, unclosed rings, coordinates outside WGS84, and arbitrary geometry", () => {
    const variants = [
      { ...response, coordinate_system: "EPSG:3857" },
      {
        ...response,
        geometry: {
          type: "Polygon",
          coordinates: [
            [
              [32, 54],
              [33, 54],
              [33, 55],
            ],
          ],
        },
      },
      {
        ...response,
        geometry: {
          type: "Polygon",
          coordinates: [
            [
              [190, 54],
              [33, 54],
              [33, 55],
              [190, 54],
            ],
          ],
        },
      },
      { ...response, geometry: { type: "GeometryCollection", geometries: [] } },
      { ...response, geometry: { type: "MultiPolygon", coordinates: [] } },
    ];
    for (const invalid of variants)
      expect(() => decodeTerritoryGeometry(invalid)).toThrow(WireError);
  });

  it("requests a URL-encoded territory ID without fabricating missing geometry", async () => {
    const fetchMock = vi.fn(async (input: string) => {
      expect(input).toBe(
        "/api/v1/territories/geometry/ru%3Aregion%3Areference",
      );
      return new Response(JSON.stringify(response));
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      const result = await getTerritoryGeometry(
        "ru:region:reference",
        new AbortController().signal,
      );
      expect(result).toMatchObject({
        kind: "ok",
        data: { territory_id: "ru:region:reference" },
      });
      expect(fetchMock.mock.calls[0]?.[0]).toBe(
        "/api/v1/territories/geometry/ru%3Aregion%3Areference",
      );
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
