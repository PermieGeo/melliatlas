import { defaultSourceDateRange, validSourceDateRange } from "./dateRange";
import type { CalendarDateRange } from "./dateRange";

export const SOURCE_DATES_KEY = "melliatlas.source-dates.v1";

export function parseSourceDatePreference(
  raw: string | null,
): CalendarDateRange | null {
  if (!raw || raw.length > 100) return null;
  try {
    const value: unknown = JSON.parse(raw);
    if (
      typeof value !== "object" ||
      value === null ||
      Array.isArray(value) ||
      Object.keys(value).some((key) => key !== "start" && key !== "end") ||
      !("start" in value) ||
      !("end" in value) ||
      typeof value.start !== "string" ||
      typeof value.end !== "string" ||
      !validSourceDateRange(value.start, value.end)
    )
      return null;
    return { start: value.start, end: value.end };
  } catch {
    return null;
  }
}

/** Persist dates only, never the user's coordinates or geocoder query. */
export function readSourceDatePreference(): CalendarDateRange {
  try {
    return (
      parseSourceDatePreference(
        window.localStorage.getItem(SOURCE_DATES_KEY),
      ) ?? defaultSourceDateRange()
    );
  } catch {
    return defaultSourceDateRange();
  }
}

export function saveSourceDatePreference(value: CalendarDateRange): void {
  if (!validSourceDateRange(value.start, value.end)) return;
  try {
    window.localStorage.setItem(SOURCE_DATES_KEY, JSON.stringify(value));
  } catch {
    // Storage denial should not prevent an on-demand analysis.
  }
}
