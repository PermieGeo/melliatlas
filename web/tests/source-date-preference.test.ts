import { afterEach, expect, it } from "vitest";
import {
  parseSourceDatePreference,
  readSourceDatePreference,
  saveSourceDatePreference,
  SOURCE_DATES_KEY,
} from "../src/geo/sourceDatePreference";

afterEach(() => window.localStorage.clear());

it("remembers a valid source date interval without storing coordinates", () => {
  const dates = { start: "2026-11-12", end: "2026-12-21" };
  saveSourceDatePreference(dates);
  expect(readSourceDatePreference()).toEqual(dates);
  expect(window.localStorage.getItem(SOURCE_DATES_KEY)).toBe(
    JSON.stringify(dates),
  );
  expect(window.localStorage.getItem(SOURCE_DATES_KEY)).not.toContain(
    "latitude",
  );
});

it("rejects malformed dates and overlong periods before trusting persisted data", () => {
  expect(
    parseSourceDatePreference('{"start":"2026-02-30","end":"2026-03-01"}'),
  ).toBeNull();
  expect(
    parseSourceDatePreference('{"start":"2026-01-01","end":"2028-01-01"}'),
  ).toBeNull();
  expect(
    parseSourceDatePreference(
      '{"start":"2026-01-01","end":"2026-02-01","latitude":12}',
    ),
  ).toBeNull();
  expect(parseSourceDatePreference("not-json")).toBeNull();
  saveSourceDatePreference({ start: "2026-11-12", end: "2028-12-21" });
  expect(window.localStorage.getItem(SOURCE_DATES_KEY)).toBeNull();
});
