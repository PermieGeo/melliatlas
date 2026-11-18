import { describe, expect, it } from "vitest";
import {
  parseDraftCoordinates,
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

describe("manual WGS84 coordinate entry", () => {
  it("accepts independent decimal fields in either locale without changing axis order", () => {
    expect(parseDraftCoordinates("54,1", "32.25")).toEqual({
      latitude: 54.1,
      longitude: 32.25,
    });
    expect(parseDraftCoordinates("-0", "+180")).toEqual({
      latitude: -0,
      longitude: 180,
    });
  });

  it("rejects ambiguous or out-of-range inputs before any server request", () => {
    const invalidInputs: [string, string][] = [
      ["", "32"],
      ["1e2", "32"],
      ["90.1", "32"],
      ["54", "181"],
      ["54.0.1", "32"],
      ["54 1", "32"],
    ];
    for (const [latitude, longitude] of invalidInputs) {
      expect(parseDraftCoordinates(latitude, longitude)).toBeNull();
    }
  });
});
