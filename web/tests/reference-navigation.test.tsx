import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "../src/App";

const referenceRegion = {
  id: "ru:region:reference",
  country: "RU",
  kind: "region",
  name: "Reference region",
  parent_id: null,
  reference_id: "ref-2026",
  valid_on: "2026-01-01",
  geometry_status: "available",
};
const referenceDistrict = {
  ...referenceRegion,
  id: "ru:district:reference",
  kind: "district",
  name: "Reference district",
  name_ru: "Тестовый район",
  parent_id: referenceRegion.id,
};
const referenceGeometry = {
  territory_id: referenceRegion.id,
  reference_id: referenceRegion.reference_id,
  coordinate_system: "EPSG:4326",
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [32, 54],
        [32.05, 54],
        [32.05, 54.05],
        [32, 54.05],
        [32, 54],
      ],
    ],
  },
};

vi.mock("../src/components/MapPanel", () => ({
  MapPanel: ({
    referenceGeometry,
    onPoint,
  }: {
    referenceGeometry: { territory_id: string } | null;
    onPoint: (position: { latitude: number; longitude: number }) => void;
  }) => (
    <>
      <div data-testid="map-reference">
        {referenceGeometry?.territory_id ?? "no-boundary"}
      </div>
      <button
        type="button"
        onClick={() => onPoint({ latitude: 54.02, longitude: 32.02 })}
      >
        Map click
      </button>
    </>
  ),
}));

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  vi.unstubAllGlobals();
});

function catalogMock(
  options: {
    districts?: "available" | "unsupported";
    geometry?: "valid" | "mismatch" | "missing";
  } = {},
) {
  const paths: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, requestOptions?: RequestInit) => {
      paths.push(input);
      if (input === "/api/v1/territories/countries") {
        return new Response(
          JSON.stringify([
            { code: "RU", name: "Russia" },
            { code: "BY", name: "Belarus" },
          ]),
        );
      }
      if (input.startsWith("/api/v1/sources?")) {
        return new Response(
          JSON.stringify([
            {
              id: "open-meteo",
              country: "RU",
              kind: "WEATHER_FORECAST",
              mode: "LIVE",
              status: "EXPERIMENTAL",
            },
          ]),
        );
      }
      if (input === "/api/v1/sources/weather/forecast") {
        const requested = JSON.parse(String(requestOptions?.body)) as {
          latitude: number;
          longitude: number;
        };
        const hours = Array.from({ length: 24 }, (_, index) => ({
          time: new Date(Date.UTC(2026, 10, 16, index)).toISOString(),
          wind_speed_kmh: 10,
          wind_direction_degrees: 220,
          wind_gusts_kmh: 14,
          precipitation_mm: 0,
        }));
        return new Response(
          JSON.stringify({
            source_id: "open-meteo:forecast",
            source_uri: "https://open-meteo.com/en/docs",
            source_mode: "LIVE",
            synthetic: false,
            captured_at: "2026-11-16T00:00:00Z",
            requested_latitude: requested.latitude,
            requested_longitude: requested.longitude,
            grid_latitude: requested.latitude,
            grid_longitude: requested.longitude,
            hours,
            uncertainties: [
              "Model forecasts do not establish pesticide drift or safety",
            ],
          }),
        );
      }
      if (input.startsWith("/api/v1/territories/regions?")) {
        return new Response(
          JSON.stringify(input.endsWith("country=RU") ? [referenceRegion] : []),
        );
      }
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response("[]");
      if (input.startsWith("/api/v1/territories/districts?")) {
        return options.districts === "available"
          ? new Response(JSON.stringify([referenceDistrict]))
          : new Response(
              JSON.stringify({
                error: {
                  code: "DISTRICT_COVERAGE_UNSUPPORTED",
                  message: "Unsupported",
                },
              }),
              { status: 409 },
            );
      }
      if (input === "/api/v1/territories/resolve-point") {
        expect(requestOptions?.method).toBe("POST");
        expect(JSON.parse(String(requestOptions?.body))).toEqual({
          country: "RU",
          latitude: 54.02,
          longitude: 32.02,
        });
        return new Response(
          JSON.stringify({
            region_id: referenceRegion.id,
            district_id: referenceDistrict.id,
          }),
        );
      }
      if (input.startsWith("/api/v1/territories/geometry/")) {
        if (options.geometry === "missing")
          return new Response(
            JSON.stringify({
              error: { code: "TERRITORY_GEOMETRY_MISSING", message: "Missing" },
            }),
            { status: 404 },
          );
        const territoryId = input.endsWith(
          encodeURIComponent(referenceDistrict.id),
        )
          ? referenceDistrict.id
          : referenceRegion.id;
        return new Response(
          JSON.stringify({
            ...referenceGeometry,
            territory_id:
              options.geometry === "mismatch" ? "by:region:wrong" : territoryId,
          }),
        );
      }
      return new Response(null, { status: 404 });
    }),
  );
  return paths;
}

async function chooseRegion() {
  await waitFor(() =>
    expect(
      (screen.getByLabelText("Область / регион") as HTMLSelectElement).disabled,
    ).toBe(false),
  );
  fireEvent.change(screen.getByLabelText("Область / регион"), {
    target: { value: referenceRegion.id },
  });
}

it("loads inline local weather automatically and only enables district-scoped analysis", async () => {
  const paths = catalogMock({ districts: "available" });
  render(<App />);
  await chooseRegion();
  await screen.findByText("ru:region:reference");
  await screen.findByText(/Сетка прогноза:/);
  expect(paths).toContain("/api/v1/sources/weather/forecast");
  const analyze = screen.getByRole("button", {
    name: "Проанализировать выбранную местность",
  });
  expect(analyze.hasAttribute("disabled")).toBe(true);
  await screen.findByRole("option", { name: "Тестовый район" });
  fireEvent.change(screen.getByLabelText("Район"), {
    target: { value: referenceDistrict.id },
  });
  await screen.findByText("ru:district:reference");
  await waitFor(() => expect(analyze.hasAttribute("disabled")).toBe(false));
  fireEvent.click(analyze);
  await screen.findByText(/Сатурн недоступен/);
  expect(paths).not.toContain("/api/v1/sources/saturn/treatments");
});

it("restores previous country, region and district after remount without storing a private point", async () => {
  const paths = catalogMock({ districts: "available" });
  const view = render(<App />);
  await chooseRegion();
  await screen.findByRole("option", { name: "Тестовый район" });
  fireEvent.change(screen.getByLabelText("Район"), {
    target: { value: referenceDistrict.id },
  });
  await screen.findByText("ru:district:reference");
  view.unmount();
  const before = paths.filter(
    (path) => path === "/api/v1/sources/weather/forecast",
  ).length;
  render(<App />);
  await screen.findByText("ru:district:reference");
  expect((screen.getByLabelText("Район") as HTMLSelectElement).value).toBe(
    referenceDistrict.id,
  );
  expect(
    (screen.getByLabelText("Область / регион") as HTMLSelectElement).value,
  ).toBe(referenceRegion.id);
  await waitFor(() =>
    expect(
      paths.filter((path) => path === "/api/v1/sources/weather/forecast")
        .length,
    ).toBeGreaterThan(before),
  );
  expect(
    window.localStorage.getItem("melliatlas.territory.selection.v1"),
  ).not.toContain("latitude");
});

it("shows API-backed geometry, supported districts, and a separate synthetic study selector", async () => {
  const paths = catalogMock({ districts: "available" });
  render(<App />);
  await chooseRegion();
  await screen.findByText("ru:region:reference");
  expect(screen.getByTestId("map-reference").textContent).toBe(
    referenceRegion.id,
  );
  await screen.findByRole("option", { name: "Тестовый район" });
  fireEvent.change(screen.getByLabelText("Район"), {
    target: { value: referenceDistrict.id },
  });
  await screen.findByText("ru:district:reference");
  expect(paths.some((path) => path.includes("districts?region_id="))).toBe(
    true,
  );
  expect(paths.some((path) => path === "/api/v1/investigations")).toBe(false);
});

it("does not draw missing or mismatched reference geometry and distinguishes unsupported districts", async () => {
  catalogMock({ districts: "unsupported", geometry: "mismatch" });
  render(<App />);
  await chooseRegion();
  expect(
    await screen.findByText(
      /Районы для этой области пока не загружены в географический справочник/,
    ),
  ).toBeTruthy();
  expect(
    await screen.findByText(/Невозможно загрузить проверенную границу/),
  ).toBeTruthy();
  expect(screen.getByTestId("map-reference").textContent).toBe("no-boundary");
});

it("drops the old boundary after the user switches country", async () => {
  catalogMock();
  render(<App />);
  await chooseRegion();
  await screen.findByText("ru:region:reference");
  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "BY" },
  });
  await waitFor(() =>
    expect(screen.getByTestId("map-reference").textContent).toBe("no-boundary"),
  );
});

it("reports HTTP 404 as missing geometry instead of drawing fictional borders", async () => {
  catalogMock({ geometry: "missing" });
  render(<App />);
  await chooseRegion();
  expect(
    await screen.findByText(
      /Для выбранной территории нет проверенной геометрии/,
    ),
  ).toBeTruthy();
  expect(screen.getByTestId("map-reference").textContent).toBe("no-boundary");
});

it("ignores geometry that resolves after a country change", async () => {
  let resolveGeometry: ((response: Response) => void) | undefined;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/v1/territories/countries") {
        return new Response(
          JSON.stringify([
            { code: "RU", name: "Russia" },
            { code: "BY", name: "Belarus" },
          ]),
        );
      }
      if (input.startsWith("/api/v1/territories/regions?")) {
        return new Response(
          JSON.stringify(input.endsWith("country=RU") ? [referenceRegion] : []),
        );
      }
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response("[]");
      if (input.startsWith("/api/v1/territories/districts?")) {
        return new Response(
          JSON.stringify({
            error: {
              code: "DISTRICT_COVERAGE_UNSUPPORTED",
              message: "Unsupported",
            },
          }),
          { status: 409 },
        );
      }
      if (input.startsWith("/api/v1/territories/geometry/")) {
        return new Promise<Response>((resolve) => {
          resolveGeometry = resolve;
        });
      }
      return new Response(null, { status: 404 });
    }),
  );
  render(<App />);
  await chooseRegion();
  await waitFor(() => expect(resolveGeometry).toBeDefined());
  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "BY" },
  });
  if (!resolveGeometry) throw new Error("Expected a pending geometry request");
  resolveGeometry(new Response(JSON.stringify(referenceGeometry)));
  await waitFor(() =>
    expect(screen.getByTestId("map-reference").textContent).toBe("no-boundary"),
  );
});

it("loads districts for the selected region and hides stale results during a region switch", async () => {
  const secondRegion = {
    ...referenceRegion,
    id: "ru:region:second",
    name: "Second region",
  };
  const secondDistrict = {
    ...referenceDistrict,
    id: "ru:district:second",
    name: "Second district",
    name_ru: null,
    parent_id: secondRegion.id,
  };
  let finishFirst: ((value: Response) => void) | undefined;
  const districtRequests: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/v1/territories/countries")
        return new Response(JSON.stringify([{ code: "RU", name: "Russia" }]));
      if (input.startsWith("/api/v1/territories/regions?"))
        return new Response(JSON.stringify([referenceRegion, secondRegion]));
      if (input.startsWith("/api/v1/territories/districts?")) {
        districtRequests.push(input);
        if (input.endsWith(encodeURIComponent(referenceRegion.id))) {
          return new Promise<Response>((resolve) => {
            finishFirst = resolve;
          });
        }
        return new Response(JSON.stringify([secondDistrict]));
      }
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response("[]");
      if (input.startsWith("/api/v1/sources?")) return new Response("[]");
      return new Response(null, { status: 404 });
    }),
  );
  render(<App />);
  await chooseRegion();
  await waitFor(() => expect(finishFirst).toBeDefined());
  fireEvent.change(screen.getByLabelText("Область / регион"), {
    target: { value: secondRegion.id },
  });
  await screen.findByRole("option", { name: "Second district" });
  if (!finishFirst)
    throw new Error("Expected an unresolved first-region response");
  finishFirst(new Response(JSON.stringify([referenceDistrict])));
  await waitFor(() => expect(districtRequests).toHaveLength(2));
  await waitFor(() =>
    expect(screen.queryByRole("option", { name: "Тестовый район" })).toBeNull(),
  );
  expect(screen.queryByRole("option", { name: "Тестовый район" })).toBeNull();
  expect(screen.getByRole("option", { name: "Second district" })).toBeTruthy();
});

it("reloads RU regions and districts after switching RU to BY and back", async () => {
  const byRegion = {
    ...referenceRegion,
    id: "by:region:vi",
    country: "BY",
    name: "Vitebsk region",
  };
  const byDistrict = {
    ...referenceDistrict,
    id: "by:district:vitebsk",
    country: "BY",
    name: "Vitebsk district",
    name_ru: null,
    parent_id: byRegion.id,
  };
  const requestedCountries: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/v1/territories/countries")
        return new Response(
          JSON.stringify([
            { code: "RU", name: "Russia" },
            { code: "BY", name: "Belarus" },
          ]),
        );
      if (input.startsWith("/api/v1/territories/regions?")) {
        const requested = new URL(input, "http://localhost").searchParams.get(
          "country",
        );
        requestedCountries.push(requested ?? "");
        return new Response(
          JSON.stringify(requested === "RU" ? [referenceRegion] : [byRegion]),
        );
      }
      if (input.startsWith("/api/v1/territories/districts?")) {
        const requested = new URL(input, "http://localhost").searchParams.get(
          "region_id",
        );
        return new Response(
          JSON.stringify(
            requested === referenceRegion.id
              ? [referenceDistrict]
              : [byDistrict],
          ),
        );
      }
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response("[]");
      if (input.startsWith("/api/v1/sources?")) return new Response("[]");
      return new Response(null, { status: 404 });
    }),
  );
  render(<App />);
  await chooseRegion();
  await screen.findByRole("option", { name: "Тестовый район" });

  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "BY" },
  });
  await screen.findByRole("option", { name: "Vitebsk region" });
  expect(
    (screen.getByLabelText("Область / регион") as HTMLSelectElement).value,
  ).toBe("");
  fireEvent.change(screen.getByLabelText("Область / регион"), {
    target: { value: byRegion.id },
  });
  await screen.findByRole("option", { name: "Vitebsk district" });

  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "RU" },
  });
  await screen.findByRole("option", { name: "Reference region" });
  expect(
    (screen.getByLabelText("Область / регион") as HTMLSelectElement).value,
  ).toBe("");
  expect(screen.queryByRole("option", { name: "Vitebsk district" })).toBeNull();
  fireEvent.change(screen.getByLabelText("Область / регион"), {
    target: { value: referenceRegion.id },
  });
  await screen.findByRole("option", { name: "Тестовый район" });
  expect(requestedCountries).toEqual(["RU", "BY", "RU"]);
});

it("allows retrying a failed region request without changing the country", async () => {
  let regionAttempts = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/v1/territories/countries")
        return new Response(JSON.stringify([{ code: "RU", name: "Russia" }]));
      if (input.startsWith("/api/v1/territories/regions?")) {
        regionAttempts += 1;
        return regionAttempts === 1
          ? new Response(
              JSON.stringify({
                error: {
                  code: "TERRITORY_REFERENCE_UNAVAILABLE",
                  message: "Database unavailable",
                },
              }),
              { status: 503 },
            )
          : new Response(JSON.stringify([referenceRegion]));
      }
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response("[]");
      if (input.startsWith("/api/v1/sources?")) return new Response("[]");
      return new Response(null, { status: 404 });
    }),
  );
  render(<App />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Повторить загрузку регионов" }),
  );
  await screen.findByRole("option", { name: "Reference region" });
  expect(regionAttempts).toBe(2);
  expect(
    (screen.getByLabelText("Область / регион") as HTMLSelectElement).disabled,
  ).toBe(false);
  expect(
    screen.queryByRole("button", { name: "Повторить загрузку регионов" }),
  ).toBeNull();
});

it("does not show a stale RU response after switching to BY", async () => {
  const byRegion = {
    ...referenceRegion,
    id: "by:region:vi",
    country: "BY",
    name: "Vitebsk region",
  };
  let releaseRU: ((response: Response) => void) | undefined;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/v1/territories/countries")
        return new Response(
          JSON.stringify([
            { code: "RU", name: "Russia" },
            { code: "BY", name: "Belarus" },
          ]),
        );
      if (input === "/api/v1/territories/regions?country=RU")
        return new Promise<Response>((resolve) => {
          releaseRU = resolve;
        });
      if (input === "/api/v1/territories/regions?country=BY")
        return new Response(JSON.stringify([byRegion]));
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response("[]");
      if (input.startsWith("/api/v1/sources?")) return new Response("[]");
      return new Response(null, { status: 404 });
    }),
  );
  render(<App />);
  await waitFor(() => expect(releaseRU).toBeDefined());
  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "BY" },
  });
  await screen.findByRole("option", { name: "Vitebsk region" });
  if (!releaseRU) throw new Error("Expected an outstanding RU request");
  await act(async () => {
    releaseRU?.(new Response(JSON.stringify([referenceRegion])));
  });
  expect(screen.queryByRole("option", { name: "Reference region" })).toBeNull();
  expect(screen.getByRole("option", { name: "Vitebsk region" })).toBeTruthy();
});

it("retries an unavailable district request for the selected RU region", async () => {
  let districtAttempts = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/v1/territories/countries")
        return new Response(JSON.stringify([{ code: "RU", name: "Russia" }]));
      if (input === "/api/v1/territories/regions?country=RU")
        return new Response(JSON.stringify([referenceRegion]));
      if (input.startsWith("/api/v1/territories/districts?")) {
        districtAttempts += 1;
        return districtAttempts === 1
          ? new Response(
              JSON.stringify({
                error: {
                  code: "TERRITORY_REFERENCE_UNAVAILABLE",
                  message: "Database unavailable",
                },
              }),
              { status: 503 },
            )
          : new Response(JSON.stringify([referenceDistrict]));
      }
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response("[]");
      if (input.startsWith("/api/v1/sources?")) return new Response("[]");
      return new Response(null, { status: 404 });
    }),
  );
  render(<App />);
  await chooseRegion();
  fireEvent.click(
    await screen.findByRole("button", { name: "Повторить загрузку районов" }),
  );
  await screen.findByRole("option", { name: "Тестовый район" });
  expect(districtAttempts).toBe(2);
  expect(
    screen.queryByRole("button", { name: "Повторить загрузку районов" }),
  ).toBeNull();
});

it("selects the containing district when the user clicks on the map", async () => {
  const paths = catalogMock({ districts: "available" });
  render(<App />);
  await waitFor(() =>
    expect(
      (screen.getByLabelText("Область / регион") as HTMLSelectElement).disabled,
    ).toBe(false),
  );
  fireEvent.click(screen.getByRole("button", { name: "Map click" }));
  await waitFor(() =>
    expect(screen.getByTestId("map-reference").textContent).toContain(
      referenceDistrict.id,
    ),
  );
  expect((screen.getByLabelText("Район") as HTMLSelectElement).value).toBe(
    referenceDistrict.id,
  );
  expect(paths).toContain("/api/v1/territories/resolve-point");
});

it("renders reviewed district translation in Russian and keeps source name in English", async () => {
  catalogMock({ districts: "available" });
  render(<App />);
  await chooseRegion();
  expect(
    await screen.findByRole("option", { name: "Тестовый район" }),
  ).toBeTruthy();
  expect(
    screen.queryByRole("option", { name: "Reference district" }),
  ).toBeNull();
  fireEvent.change(screen.getByLabelText("Язык"), { target: { value: "en" } });
  expect(
    screen.getByRole("option", { name: "Reference district" }),
  ).toBeTruthy();
});

it("reconciles edited source interval and keeps Analyze available", async () => {
  catalogMock({ districts: "available" });
  render(<App />);
  await chooseRegion();
  await screen.findByRole("option", { name: "Тестовый район" });
  fireEvent.change(screen.getByLabelText("Район"), {
    target: { value: referenceDistrict.id },
  });
  const analyze = screen.getByRole("button", {
    name: "Проанализировать выбранную местность",
  });
  await waitFor(() => expect(analyze.hasAttribute("disabled")).toBe(false));
  fireEvent.change(screen.getByLabelText("Сатурн: дата начала"), {
    target: { value: "2027-01-15" },
  });
  expect(
    (screen.getByLabelText("Сатурн: дата окончания") as HTMLInputElement).value,
  ).toBe("2027-02-15");
  expect(analyze.hasAttribute("disabled")).toBe(false);
  expect(screen.getByText("Исходная точка")).toBeTruthy();
  expect(
    screen.getByRole("heading", { name: "Поиск медоносных угодий" }),
  ).toBeTruthy();
  expect(screen.queryByText("Версия справочника:")).toBeNull();
  expect(
    screen.queryByText("Необязательное демонстрационное исследование"),
  ).toBeNull();
});
