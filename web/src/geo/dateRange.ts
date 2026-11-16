/** Default local calendar window; date-only source filters do not imply spraying dates. */
export interface CalendarDateRange {
  start: string;
  end: string;
}
const MAX_SOURCE_WINDOW_YEARS = 1;
const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;

function localDate(value: Date): string {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
}

export function defaultSourceDateRange(
  now: Date = new Date(),
): CalendarDateRange {
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const year = start.getFullYear();
  const month = start.getMonth();
  const lastNextMonthDay = new Date(year, month + 2, 0).getDate();
  const end = new Date(
    year,
    month + 1,
    Math.min(start.getDate(), lastNextMonthDay),
  );
  return { start: localDate(start), end: localDate(end) };
}

function parseSourceDate(value: string): Date | null {
  if (!DATE_ONLY.test(value)) return null;
  const date = new Date(`${value}T00:00:00.000Z`);
  return !Number.isNaN(date.getTime()) &&
    date.toISOString().slice(0, 10) === value
    ? date
    : null;
}

function shiftSourceYear(date: Date, years: number): Date {
  const year = date.getUTCFullYear() + years * MAX_SOURCE_WINDOW_YEARS;
  const month = date.getUTCMonth();
  const lastDay = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
  return new Date(Date.UTC(year, month, Math.min(date.getUTCDate(), lastDay)));
}

export function validSourceDateRange(start: string, end: string): boolean {
  const first = parseSourceDate(start);
  const last = parseSourceDate(end);
  if (!first || !last || first > last) return false;
  return last <= shiftSourceYear(first, MAX_SOURCE_WINDOW_YEARS);
}

/** Keep manually edited dates within the server's one-calendar-year source limit. */
export function updateSourceDateRange(
  current: CalendarDateRange,
  changed: "start" | "end",
  value: string,
): CalendarDateRange {
  const updated = { ...current, [changed]: value };
  const date = parseSourceDate(value);
  if (!date || validSourceDateRange(updated.start, updated.end)) return updated;
  if (changed === "start") {
    const previousEnd = parseSourceDate(current.end);
    if (previousEnd && previousEnd < date) {
      const lastNextMonthDay = new Date(
        Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 2, 0),
      ).getUTCDate();
      const nextMonth = new Date(
        Date.UTC(
          date.getUTCFullYear(),
          date.getUTCMonth() + 1,
          Math.min(date.getUTCDate(), lastNextMonthDay),
        ),
      );
      updated.end = nextMonth.toISOString().slice(0, 10);
    } else {
      updated.end = shiftSourceYear(date, MAX_SOURCE_WINDOW_YEARS)
        .toISOString()
        .slice(0, 10);
    }
  } else {
    const previousStart = parseSourceDate(current.start);
    if (previousStart && previousStart > date) {
      updated.start = value;
    } else {
      const earliest = shiftSourceYear(date, -MAX_SOURCE_WINDOW_YEARS);
      if (!validSourceDateRange(earliest.toISOString().slice(0, 10), value)) {
        // An end date of February 29 needs March 1 in the previous year.
        earliest.setUTCDate(earliest.getUTCDate() + 1);
      }
      updated.start = earliest.toISOString().slice(0, 10);
    }
  }
  return updated;
}
