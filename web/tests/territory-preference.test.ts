import { afterEach, expect, it, vi } from "vitest";
import {
  parseTerritoryPreference,
  readTerritoryPreference,
  saveTerritoryPreference,
  TERRITORY_PREFERENCE_KEY,
} from "../src/geo/territoryPreference";
import {
  defaultSourceDateRange,
  updateSourceDateRange,
  validSourceDateRange,
} from "../src/geo/dateRange";
import { isInsideArea, representativePoint } from "../src/geo/selection";

afterEach(() => vi.unstubAllGlobals());

it("persists only public country/region/district IDs and rejects malformed preferences", () => {
  const stored = new Map<string, string>();
  vi.stubGlobal("window", {
    localStorage: {
      getItem: (key: string) => stored.get(key) ?? null,
      setItem: (key: string, value: string) => {
        stored.set(key, value);
      },
    },
  });
  const selection = {
    country: "RU",
    regionId: "ru:region:smo",
    districtId: "ru:district:example",
  };
  saveTerritoryPreference(selection);
  expect(readTerritoryPreference()).toEqual(selection);
  expect(stored.get(TERRITORY_PREFERENCE_KEY)).not.toContain("latitude");
  expect(
    parseTerritoryPreference(
      '{"country":"RU","regionId":"by:region:vi","districtId":""}',
    ),
  ).toBeNull();
  expect(
    parseTerritoryPreference(
      '{"country":"RU","regionId":"ru:region:smo","districtId":"ru:district:example","latitude":55}',
    ),
  ).toBeNull();
  expect(parseTerritoryPreference("{")).toBeNull();
});

it("uses today through one calendar month, including end-of-month rollover", () => {
  expect(defaultSourceDateRange(new Date(2026, 0, 31, 12))).toEqual({
    start: "2026-01-31",
    end: "2026-02-28",
  });
  expect(defaultSourceDateRange(new Date(2026, 10, 16, 12))).toEqual({
    start: "2026-11-16",
    end: "2026-12-16",
  });
  expect(validSourceDateRange("2026-11-16", "2026-12-16")).toBe(true);
  expect(validSourceDateRange("2026-11-16", "2026-12-20")).toBe(false);
  expect(validSourceDateRange("2026-02-31", "2026-03-01")).toBe(false);
  expect(validSourceDateRange("2026-11-16", "2026-11-15")).toBe(false);
});

it("takes a point inside a concave reference area, not outside its bounding box", () => {
  const shape = {
    type: "Polygon" as const,
    coordinates: [
      [
        [0, 0] as [number, number],
        [4, 0] as [number, number],
        [4, 1] as [number, number],
        [1, 1] as [number, number],
        [1, 4] as [number, number],
        [0, 4] as [number, number],
        [0, 0] as [number, number],
      ],
    ],
  };
  const point = representativePoint(shape);
  expect(point).not.toBeNull();
  expect(isInsideArea(point!, shape)).toBe(true);
});

it("keeps manual source-date edits analyzable without widening the 31-day backend bound", () => {
  const original = { start: "2026-11-16", end: "2026-12-16" };
  const laterStart = updateSourceDateRange(original, "start", "2027-01-15");
  expect(laterStart).toEqual({ start: "2027-01-15", end: "2027-02-15" });
  expect(validSourceDateRange(laterStart.start, laterStart.end)).toBe(true);
  const laterEnd = updateSourceDateRange(original, "end", "2027-03-01");
  expect(laterEnd).toEqual({ start: "2027-01-29", end: "2027-03-01" });
  expect(validSourceDateRange(laterEnd.start, laterEnd.end)).toBe(true);
  const nearby = updateSourceDateRange(original, "start", "2026-11-20");
  expect(nearby.end).toBe("2026-12-16");
  expect(validSourceDateRange("2026-11-15", "2026-11-14")).toBe(false);
  expect(validSourceDateRange("2026-11-01", "2027-01-01")).toBe(false);
});
