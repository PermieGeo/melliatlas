import {
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
  }: {
    referenceGeometry: { territory_id: string } | null;
  }) => (
    <div data-testid="map-reference">
      {referenceGeometry?.territory_id ?? "no-boundary"}
    </div>
  ),
}));

afterEach(() => {
  cleanup();
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

it("loads a reviewed region automatically and triggers the live forecast with one action", async () => {
  const paths = catalogMock({ districts: "available" });
  render(<App />);
  await chooseRegion();
  await screen.findByText("ru:region:reference");
  const analyze = screen.getByRole("button", {
    name: "Проанализировать выбранную местность",
  });
  await waitFor(() => expect(analyze.hasAttribute("disabled")).toBe(false));
  expect(paths).not.toContain("/api/v1/sources/weather/forecast");
  fireEvent.click(analyze);
  await screen.findByText("Почасовой прогноз (24 ч)");
  expect(paths).toContain("/api/v1/sources/weather/forecast");
  expect(paths).not.toContain("/api/v1/sources/saturn/treatments");
});

it("shows API-backed geometry, supported districts, and a separate synthetic study selector", async () => {
  const paths = catalogMock({ districts: "available" });
  render(<App />);
  await chooseRegion();
  await screen.findByText("ru:region:reference");
  expect(screen.getByTestId("map-reference").textContent).toBe(
    referenceRegion.id,
  );
  await screen.findByRole("option", { name: "Reference district" });
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
