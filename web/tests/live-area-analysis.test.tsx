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
  districtId: "ru:district:smolensk-test",
  dateStart: "2026-11-16",
  dateEnd: "2026-12-16",
};
const page = {
  source_id: "saturn:public-beekeeper-portal",
  country: "RU",
  region_code: 55,
  region_id: request.regionId,
  district_id: request.districtId,
  date_start: request.dateStart,
  date_end: request.dateEnd,
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

it("loads only a district-scoped Saturn page after analysis", async () => {
  const requests: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, options?: RequestInit) => {
      requests.push(path);
      if (path.endsWith("/saturn/treatments")) {
        expect(JSON.parse(String(options?.body))).toEqual({
          country: "RU",
          region_id: request.regionId,
          district_id: request.districtId,
          date_start: request.dateStart,
          date_end: request.dateEnd,
          page_number: 0,
        });
        return new Response(JSON.stringify(page));
      }
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
  expect(requests).not.toContain("/api/v1/sources/weather/forecast");
  expect(screen.getByText(/Запрашивается только район/)).toBeTruthy();
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
      return new Response(null, { status: 404 });
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
  await screen.findByText(/Saturn is not available/);
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

it("never falls back to region-wide Saturn when district is unmapped", async () => {
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
  expect(screen.queryByText("Почасовой прогноз (24 ч)")).toBeNull();
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
          district_id: string;
          date_start: string;
          date_end: string;
        };
        expect(requestBody.district_id).toBe(request.districtId);
        expect(requestBody.date_start).toBe(request.dateStart);
        expect(requestBody.date_end).toBe(request.dateEnd);
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

it("clearly reports zero identified notices without claiming pesticide safety", async () => {
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
          ]),
        );
      if (path.endsWith("/saturn/treatments"))
        return new Response(
          JSON.stringify({ ...page, next_page: null, total_elements: 0 }),
        );
      return new Response(null, { status: 404 });
    }),
  );
  render(
    <LiveAreaAnalysis
      locale="ru"
      country="RU"
      regionId={request.regionId}
      request={request}
      onNotices={vi.fn()}
    />,
  );
  expect(await screen.findByText("Нет распознанных записей")).toBeTruthy();
  expect(screen.getByText(/Это не означает отсутствия обработок/)).toBeTruthy();
});
