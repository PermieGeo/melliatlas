import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { LiveAreaAnalysis } from "../src/components/LiveAreaAnalysis";
import type { AreaAnalysisRequest } from "../src/components/LiveAreaAnalysis";
import { areaSize, isInsideArea } from "../src/geo/selection";

const request: AreaAnalysisRequest = {
  sequence: 1,
  country: "RU",
  regionId: "ru:region:smo",
  point: { latitude: 54, longitude: 32 },
};
const hours = Array.from({ length: 24 }, (_, index) => ({
  time: new Date(Date.UTC(2026, 10, 16, index)).toISOString(),
  wind_speed_kmh: 10,
  wind_direction_degrees: 180,
  wind_gusts_kmh: 13,
  precipitation_mm: 0,
}));
const forecast = {
  source_id: "open-meteo:forecast",
  source_uri: "https://open-meteo.com/en/docs",
  source_mode: "LIVE",
  synthetic: false,
  captured_at: "2026-11-16T00:00:00Z",
  requested_latitude: 54,
  requested_longitude: 32,
  grid_latitude: 54.1,
  grid_longitude: 32.1,
  hours,
  uncertainties: ["Model forecasts do not establish pesticide drift or safety"],
};
const page = {
  source_id: "saturn:public-beekeeper-portal",
  country: "RU",
  region_code: 55,
  region_id: request.regionId,
  captured_at: "2026-11-16T00:00:00Z",
  page_number: 0,
  next_page: 1,
  total_elements: 230,
  unidentified_records: 0,
  coverage_complete: false,
  notices: [],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("loads RU Saturn and weather together after one analysis action", async () => {
  const requests: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string) => {
      requests.push(path);
      if (path.startsWith("/api/v1/sources?"))
        return new Response(
          JSON.stringify([
            {
              id: "saturn",
              country: "RU",
              kind: "TREATMENT_NOTICE",
              mode: "LIVE",
              status: "EXPERIMENTAL",
            },
            {
              id: "open-meteo",
              country: "RU",
              kind: "WEATHER_FORECAST",
              mode: "LIVE",
              status: "EXPERIMENTAL",
            },
          ]),
        );
      if (path.endsWith("/saturn/treatments"))
        return new Response(JSON.stringify(page));
      if (path.endsWith("/weather/forecast"))
        return new Response(JSON.stringify(forecast));
      return new Response(null, { status: 404 });
    }),
  );
  const onNotices = vi.fn();
  const view = render(
    <LiveAreaAnalysis
      country="RU"
      regionId={request.regionId}
      locale="ru"
      request={null}
      onNotices={onNotices}
    />,
  );
  await waitFor(() => expect(requests).toHaveLength(1));
  expect(requests.every((path) => path.startsWith("/api/v1/sources?"))).toBe(
    true,
  );
  view.rerender(
    <LiveAreaAnalysis
      country="RU"
      regionId={request.regionId}
      locale="ru"
      request={request}
      onNotices={onNotices}
    />,
  );
  await screen.findByText(/Загружено страниц: 1/);
  expect(requests).toContain("/api/v1/sources/saturn/treatments");
  expect(requests).toContain("/api/v1/sources/weather/forecast");
  expect(
    screen.getByText(/Частичная выборка не подтверждает отсутствие обработок/),
  ).toBeTruthy();
  expect(
    screen.queryByRole("button", { name: /Загрузить одну страницу/ }),
  ).toBeNull();
});

it("never attempts RU-only Saturn for BY and ignores obsolete results", async () => {
  const paths: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string) => {
      paths.push(path);
      if (path.startsWith("/api/v1/sources?"))
        return new Response(
          JSON.stringify([
            {
              id: "open-meteo",
              country: "BY",
              kind: "WEATHER_FORECAST",
              mode: "LIVE",
              status: "EXPERIMENTAL",
            },
          ]),
        );
      return new Response(JSON.stringify(forecast));
    }),
  );
  render(
    <LiveAreaAnalysis
      country="BY"
      regionId="by:region:vi"
      locale="en"
      request={{ ...request, country: "BY", regionId: "by:region:vi" }}
      onNotices={vi.fn()}
    />,
  );
  await screen.findByText("Hourly weather forecast (24 h)");
  expect(paths).not.toContain("/api/v1/sources/saturn/treatments");
});

it("requires a real polygon point rather than merely its bounding box", () => {
  const shape = {
    type: "Polygon" as const,
    coordinates: [
      [
        [30, 54] as [number, number],
        [33, 54] as [number, number],
        [33, 56] as [number, number],
        [30, 54] as [number, number],
      ],
    ],
  };
  expect(areaSize(shape)?.widthKm).toBeGreaterThan(100);
  expect(isInsideArea({ latitude: 54.4, longitude: 31.5 }, shape)).toBe(true);
  expect(isInsideArea({ latitude: 55.5, longitude: 30.1 }, shape)).toBe(false);
});

it("keeps weather available when a region has no reviewed Saturn mapping", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string) => {
      if (path.startsWith("/api/v1/sources?"))
        return new Response(
          JSON.stringify([
            {
              id: "saturn",
              country: "RU",
              kind: "TREATMENT_NOTICE",
              mode: "LIVE",
              status: "EXPERIMENTAL",
            },
            {
              id: "open-meteo",
              country: "RU",
              kind: "WEATHER_FORECAST",
              mode: "LIVE",
              status: "EXPERIMENTAL",
            },
          ]),
        );
      if (path.endsWith("/saturn/treatments")) {
        return new Response(
          JSON.stringify({
            error: { code: "SOURCE_REGION_UNMAPPED", message: "No mapping" },
          }),
          { status: 409 },
        );
      }
      if (path.endsWith("/weather/forecast"))
        return new Response(JSON.stringify(forecast));
      return new Response(null, { status: 404 });
    }),
  );
  render(
    <LiveAreaAnalysis
      country="RU"
      regionId={request.regionId}
      locale="ru"
      request={request}
      onNotices={vi.fn()}
    />,
  );
  await screen.findByText(/нет проверенного кода Сатурна/);
  expect(screen.getByText("Почасовой прогноз (24 ч)")).toBeTruthy();
});

it("retrieves later pages only when requested and accumulates mapped field records", async () => {
  const calls: number[] = [];
  const field = {
    record_id: "field-1",
    plan_id: "plan-1",
    country: "RU",
    source_id: page.source_id,
    source_uri: "https://bee.fgis-saturn.ru/",
    source_mode: "LIVE",
    synthetic: false,
    captured_at: page.captured_at,
    published_at: null,
    scheduled_start: null,
    scheduled_end: null,
    revised: false,
    cadastral_number: null,
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [32, 54],
          [33, 54],
          [33, 55],
          [32, 54],
        ],
      ],
    },
    products: [],
    uncertainties: [],
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, init?: RequestInit) => {
      if (path.startsWith("/api/v1/sources?"))
        return new Response(
          JSON.stringify([
            {
              id: "saturn",
              country: "RU",
              kind: "TREATMENT_NOTICE",
              mode: "LIVE",
              status: "EXPERIMENTAL",
            },
          ]),
        );
      if (path.endsWith("/saturn/treatments")) {
        const requestBody = JSON.parse(String(init?.body)) as {
          page_number: number;
        };
        calls.push(requestBody.page_number);
        return new Response(
          JSON.stringify({
            ...page,
            page_number: requestBody.page_number,
            next_page: requestBody.page_number === 0 ? 1 : null,
            total_elements: 11,
            notices: requestBody.page_number === 0 ? [] : [field],
          }),
        );
      }
      return new Response(null, { status: 404 });
    }),
  );
  const onNotices = vi.fn();
  render(
    <LiveAreaAnalysis
      country="RU"
      regionId={request.regionId}
      locale="en"
      request={request}
      onNotices={onNotices}
    />,
  );
  await screen.findByText(/Fetched 1 page/);
  expect(calls).toEqual([0]);
  fireEvent.click(screen.getByRole("button", { name: "Load next 10 records" }));
  await screen.findByText(/Field polygons in fetched records: 1/);
  expect(calls).toEqual([0, 1]);
  expect(onNotices).toHaveBeenLastCalledWith([
    expect.objectContaining({ record_id: "field-1" }),
  ]);
  expect(
    screen.queryByRole("button", { name: "Load next 10 records" }),
  ).toBeNull();
});
