/** Default local calendar window; date-only source filters do not imply spraying dates. */
export interface CalendarDateRange {
  start: string;
  end: string;
}
const MAX_SOURCE_WINDOW_DAYS = 31;
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

export function validSourceDateRange(start: string, end: string): boolean {
  if (!DATE_ONLY.test(start) || !DATE_ONLY.test(end)) return false;
  const first = new Date(`${start}T00:00:00.000Z`);
  const last = new Date(`${end}T00:00:00.000Z`);
  if (
    Number.isNaN(first.valueOf()) ||
    Number.isNaN(last.valueOf()) ||
    first.toISOString().slice(0, 10) !== start ||
    last.toISOString().slice(0, 10) !== end
  )
    return false;
  const diff = (last.valueOf() - first.valueOf()) / 86_400_000;
  return diff >= 0 && diff <= MAX_SOURCE_WINDOW_DAYS;
}
