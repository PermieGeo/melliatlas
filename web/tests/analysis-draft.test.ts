import { describe, expect, it } from "vitest";
import {
  provisionalDraftRectangle,
  validDraftDimension,
} from "../src/geo/analysisDraft";

describe("unsaved WGS84 analysis draft", () => {
  it("constructs a bounded 15 km rectangle without interpreting longitude degrees as kilometers", () => {
    const bounds = provisionalDraftRectangle(
      { longitude: 32, latitude: 54 },
      15,
      15,
    );
    expect(bounds).not.toBeNull();
    if (!bounds) throw new Error("Missing bounds");
    expect(bounds.longitudeRanges).toHaveLength(1);
    const lonRange = bounds.longitudeRanges[0];
    expect(lonRange).toBeDefined();
    if (!lonRange) throw new Error("Missing longitude range");
    expect((lonRange[0] + lonRange[1]) / 2).toBeCloseTo(32, 8);
    expect(lonRange[1] - lonRange[0]).toBeGreaterThan(
      bounds.north - bounds.south,
    );
  });

  it("splits the antimeridian rather than drawing across the world", () => {
    const bounds = provisionalDraftRectangle(
      { longitude: 179.99, latitude: 10 },
      15,
      15,
    );
    expect(bounds?.longitudeRanges).toHaveLength(2);
    expect(bounds?.longitudeRanges[0]?.[1]).toBe(180);
    expect(bounds?.longitudeRanges[1]?.[0]).toBe(-180);
  });

  it("rejects invalid coordinates, polar rectangles, dimensions and non-finite inputs", () => {
    for (const dimension of [0, -1, 30.1, NaN, Infinity])
      expect(validDraftDimension(dimension)).toBe(false);
    expect(validDraftDimension(30)).toBe(true);
    expect(
      provisionalDraftRectangle({ longitude: 32, latitude: 90 }, 15, 15),
    ).toBeNull();
    expect(
      provisionalDraftRectangle({ longitude: 180.1, latitude: 54 }, 15, 15),
    ).toBeNull();
    expect(
      provisionalDraftRectangle({ longitude: 32, latitude: 54 }, 31, 15),
    ).toBeNull();
  });
});
