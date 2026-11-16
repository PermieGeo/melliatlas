import { afterEach, expect, it, vi } from "vitest";
import {
  DEFAULT_VIEWPORT,
  parseMapViewport,
  readMapViewport,
  saveMapViewport,
  VIEWPORT_STORAGE_KEY,
} from "../src/geo/viewport";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("accepts an ordinary saved WGS84 Web Mercator camera", () => {
  expect(
    parseMapViewport('{"latitude":54.7812,"longitude":32.0456,"zoom":9}'),
  ).toEqual({
    latitude: 54.7812,
    longitude: 32.0456,
    zoom: 9,
  });
  expect(DEFAULT_VIEWPORT.zoom).toBeGreaterThanOrEqual(2);
});

it.each([
  null,
  "",
  "not json",
  "[]",
  "null",
  "{}",
  '{"latitude":91,"longitude":32,"zoom":5}',
  '{"latitude":85.1,"longitude":32,"zoom":5}',
  '{"latitude":55,"longitude":181,"zoom":5}',
  '{"latitude":55,"longitude":32,"zoom":19}',
  '{"latitude":55,"longitude":32,"zoom":4.5}',
  '{"latitude":"55","longitude":32,"zoom":5}',
])("rejects invalid or unexpected camera data: %s", (raw) => {
  expect(parseMapViewport(raw)).toBeNull();
});

it("ignores unknown browser-stored fields rather than returning a private marker", () => {
  expect(
    parseMapViewport(
      '{"latitude":55,"longitude":32,"zoom":5,"point":"private"}',
    ),
  ).toEqual({ latitude: 55, longitude: 32, zoom: 5 });
});

it("persists the map viewport locally without persisting point metadata", () => {
  const values = new Map<string, string>();
  vi.stubGlobal("window", {
    localStorage: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
    },
  });
  saveMapViewport({ latitude: 54.7821234, longitude: 32.0456789, zoom: 8 });
  expect(values.get(VIEWPORT_STORAGE_KEY)).toBe(
    '{"latitude":54.7821,"longitude":32.0457,"zoom":8}',
  );
  expect(readMapViewport()).toEqual({
    latitude: 54.7821,
    longitude: 32.0457,
    zoom: 8,
  });
});

it("does not fail if the browser blocks storage", () => {
  vi.stubGlobal("window", {
    localStorage: {
      getItem: () => {
        throw new Error("Storage denied");
      },
      setItem: () => {
        throw new Error("Storage denied");
      },
    },
  });
  expect(readMapViewport()).toBeNull();
  expect(() => saveMapViewport(DEFAULT_VIEWPORT)).not.toThrow();
});
