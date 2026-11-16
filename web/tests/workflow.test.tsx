import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "../src/App";
import fixture from "./fixtures/combined.json";

const jointScenario = {
  id: "synthetic-ru-2026-v04-ecology-treatment",
  name: "Ecology and reported treatments (fictional)",
  country: "RU",
  territory_id: "ru:region:smolensk",
  territory_name: "Smolensk region (fictional)",
  source_mode: "SYNTHETIC",
  season_start: "2026-05-01",
  season_end: "2026-08-15",
  is_default: true,
};

async function waitForDemo() {
  const summary = screen.getByText(
    "Необязательное демонстрационное исследование",
  );
  const details = summary.closest("details");
  if (details && !details.open) fireEvent.click(summary);
  await waitFor(() =>
    expect(
      screen
        .getByRole("button", { name: /Исследовать размещение/ })
        .hasAttribute("disabled"),
    ).toBe(false),
  );
}

vi.mock("../src/components/MapPanel", () => ({
  MapPanel: ({
    onSelect,
    onPoint,
  }: {
    onSelect: (id: string) => void;
    onPoint: (point: { longitude: number; latitude: number }) => void;
  }) => (
    <div data-testid="map-stub">
      <button onClick={() => onSelect("fixture-site-beta")}>
        Выбрать на карте вторую стоянку
      </button>
      <button
        onClick={() => onPoint({ longitude: 32.12345, latitude: 54.23456 })}
      >
        Выбрать исходную точку
      </button>
    </div>
  ),
}));

afterEach(() => {
  window.localStorage.clear();
  cleanup();
  vi.unstubAllGlobals();
});

function mockApi() {
  const calls: Array<{ path: string; body?: string }> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, options?: RequestInit) => {
      calls.push({
        path: input,
        body: typeof options?.body === "string" ? options.body : undefined,
      });
      if (input === "/api/v1/territories/countries")
        return new Response(
          JSON.stringify([
            { code: "RU", name: "Russia" },
            { code: "BY", name: "Belarus" },
          ]),
        );
      if (input.startsWith("/api/v1/territories/regions"))
        return new Response(
          JSON.stringify({
            error: {
              code: "TERRITORY_REFERENCE_UNAVAILABLE",
              message: "No reference",
            },
          }),
          { status: 503 },
        );
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response(
          JSON.stringify(input.endsWith("country=RU") ? [jointScenario] : []),
        );
      if (input === "/api/v1/investigations")
        return new Response(
          JSON.stringify({
            ...fixture,
            status: "QUEUED",
            outcome: null,
            plan: null,
            replanning: null,
            treatment_review: null,
            evidence: [],
          }),
          { status: 202 },
        );
      if (input.startsWith("/api/v1/investigations/"))
        return new Response(JSON.stringify(fixture));
      return new Response(null, { status: 404 });
    }),
  );
  return calls;
}

it("runs the joint fixture, shows attributed findings and synchronizes map/timeline selection", async () => {
  const calls = mockApi();
  render(<App />);
  await waitForDemo();
  expect(screen.getByText(/Только вымышленные данные/)).toBeTruthy();
  expect(
    await screen.findByText(/Справочник регионов недоступен/),
  ).toBeTruthy();
  await waitForDemo();
  fireEvent.click(
    screen.getByRole("button", { name: /Исследовать размещение/ }),
  );
  expect(
    await screen.findByText(/Предварительный план сформирован/),
  ).toBeTruthy();
  expect(
    screen.getAllByText(/fixture-site-alpha-treatment-alternative/).length,
  ).toBeGreaterThan(0);
  expect(screen.getByText(/Химические обработки/)).toBeTruthy();
  expect(screen.getByText(/Экология/)).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: "Выбрать на карте вторую стоянку" }),
  );
  expect(
    screen
      .getByRole("button", { name: /Стоянка 2,/ })
      .getAttribute("aria-pressed"),
  ).toBe("true");
  fireEvent.click(screen.getByRole("button", { name: /Стоянка 3,/ }));
  expect(screen.getByText(/^Стоянка:/).textContent).toContain(
    "fixture-site-gamma",
  );
  expect(
    calls.filter((item) => item.path === "/api/v1/investigations"),
  ).toHaveLength(1);
  expect(calls.some((item) => item.path.includes("starting_point"))).toBe(
    false,
  );
});

it("sends a selected coordinate only in the body, never in URLs or browser storage", async () => {
  const calls = mockApi();
  render(<App />);
  fireEvent.click(
    screen.getByRole("button", { name: "Выбрать исходную точку" }),
  );
  await waitForDemo();
  fireEvent.click(
    screen.getByRole("button", { name: /Исследовать размещение/ }),
  );
  await screen.findByText(/Предварительный план сформирован/);
  const created = calls.find(
    (entry) => entry.path === "/api/v1/investigations",
  );
  expect(created?.body).toContain('"longitude":32.12345');
  expect(calls.every((entry) => !entry.path.includes("32.12345"))).toBe(true);
  expect(window.location.search).toBe("");
});

it("keeps technical investigation IDs off the beekeeper-facing screen", async () => {
  mockApi();
  render(<App />);
  await screen.findByLabelText("Страна");
  expect(screen.queryByLabelText("Открыть по ID")).toBeNull();
  expect(screen.queryByText("Перейти к реальным источникам")).toBeNull();
  expect(
    screen
      .getByRole("button", { name: "Проанализировать выбранную местность" })
      .hasAttribute("disabled"),
  ).toBe(true);
});

it("disables an unsupported BY demonstration and ignores a stale result after country switch", async () => {
  mockApi();
  render(<App />);
  await waitForDemo();
  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "BY" },
  });
  await waitFor(() =>
    expect(
      screen.getByText(/Демонстрационный планировщик отключён/),
    ).toBeTruthy(),
  );
  expect(screen.queryByLabelText("Территория")).toBeNull();
  expect(
    screen.queryByRole("button", { name: /Исследовать размещение/ }),
  ).toBeNull();
  expect(
    screen.queryByRole("link", { name: "Перейти к реальным источникам" }),
  ).toBeNull();
});

it("ignores a delayed completed response after the user changes country", async () => {
  const pending: { resolve?: (response: Response) => void } = {};
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
      if (input.startsWith("/api/v1/territories/regions")) {
        return new Response(
          JSON.stringify({
            error: {
              code: "TERRITORY_REFERENCE_UNAVAILABLE",
              message: "No reference",
            },
          }),
          { status: 503 },
        );
      }
      if (input.startsWith("/api/v1/investigations/scenarios?")) {
        return new Response(
          JSON.stringify(input.endsWith("country=RU") ? [jointScenario] : []),
        );
      }
      if (input === "/api/v1/investigations") {
        return new Promise<Response>((resolve) => {
          pending.resolve = resolve;
        });
      }
      return new Response(JSON.stringify(fixture));
    }),
  );
  render(<App />);
  await waitForDemo();
  fireEvent.click(
    screen.getByRole("button", { name: /Исследовать размещение/ }),
  );
  await waitFor(() => expect(pending.resolve).toBeDefined());
  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "BY" },
  });
  pending.resolve?.(new Response(JSON.stringify(fixture), { status: 202 }));
  await waitFor(() =>
    expect(screen.queryByText(/Предварительный план сформирован/)).toBeNull(),
  );
  await waitFor(() =>
    expect(
      screen.queryByRole("button", { name: /Исследовать размещение/ }),
    ).toBeNull(),
  );
});

it("distinguishes completed insufficient evidence from a backend failure", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/v1/territories/countries")
        return new Response(JSON.stringify([{ code: "RU", name: "Russia" }]));
      if (input.startsWith("/api/v1/territories/regions"))
        return new Response(JSON.stringify([]));
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response(
          JSON.stringify(input.endsWith("country=RU") ? [jointScenario] : []),
        );
      if (input === "/api/v1/investigations")
        return new Response(
          JSON.stringify({
            ...fixture,
            status: "QUEUED",
            plan: null,
            outcome: null,
            replanning: null,
            treatment_review: null,
            evidence: [],
          }),
          { status: 202 },
        );
      return new Response(
        JSON.stringify({
          ...fixture,
          outcome: "INSUFFICIENT_EVIDENCE",
          plan: null,
        }),
      );
    }),
  );
  render(<App />);
  await waitForDemo();
  fireEvent.click(
    screen.getByRole("button", { name: /Исследовать размещение/ }),
  );
  expect(
    await screen.findByText(/недостаточно проверенных стоянок/),
  ).toBeTruthy();
  expect(screen.queryByText(/Предварительный план сформирован/)).toBeNull();
});

it("switches RU/EN without discarding the investigation and keeps source evidence intact", async () => {
  mockApi();
  render(<App />);
  await waitForDemo();
  fireEvent.change(screen.getByLabelText("Язык"), { target: { value: "en" } });
  expect(screen.getByLabelText("Country")).toBeTruthy();
  expect(screen.getByLabelText("Analysis source")).toBeTruthy();
  expect(screen.getByLabelText("Season start")).toHaveProperty(
    "value",
    "2026-05-01",
  );
  fireEvent.click(
    screen.getByRole("button", { name: /Investigate placement/ }),
  );
  expect(await screen.findByText(/Provisional plan prepared/)).toBeTruthy();
  expect(screen.getByText("Reported treatments")).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Language"), {
    target: { value: "ru" },
  });
  expect(screen.getByText(/Предварительный план сформирован/)).toBeTruthy();
});

it("uses server-supplied country, scenario, territory and season without RU-specific branches", async () => {
  const payloads: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, options?: RequestInit) => {
      if (input === "/api/v1/territories/countries")
        return new Response(JSON.stringify([{ code: "PL", name: "Poland" }]));
      if (input.startsWith("/api/v1/territories/regions"))
        return new Response(JSON.stringify([]));
      if (input.startsWith("/api/v1/investigations/scenarios?"))
        return new Response(
          JSON.stringify(
            input.endsWith("country=PL")
              ? [
                  {
                    ...jointScenario,
                    id: "fictional-pl-2030",
                    country: "PL",
                    territory_id: "pl:region:fixture",
                    territory_name: "Fictional region",
                    season_start: "2030-06-01",
                    season_end: "2030-09-15",
                  },
                ]
              : [],
          ),
        );
      if (input === "/api/v1/investigations") {
        if (typeof options?.body === "string") payloads.push(options.body);
        return new Response(JSON.stringify({ ...fixture, status: "FAILED" }), {
          status: 202,
        });
      }
      return new Response(JSON.stringify(fixture));
    }),
  );
  render(<App />);
  await waitForDemo();
  expect(screen.getByLabelText("Страна")).toHaveProperty("value", "PL");
  expect(screen.getByLabelText("Начало сезона")).toHaveProperty(
    "value",
    "2030-06-01",
  );
  fireEvent.click(
    screen.getByRole("button", { name: /Исследовать размещение/ }),
  );
  await waitFor(() => expect(payloads).toHaveLength(1));
  expect(JSON.parse(payloads[0] ?? "{}")).toMatchObject({
    country: "PL",
    territory_id: "pl:region:fixture",
    scenario_id: "fictional-pl-2030",
    season_start: "2030-06-01",
    season_end: "2030-09-15",
  });
});

it("keeps RU Saturn and RU/BY weather accessible without synthetic scenarios or regional references", async () => {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      calls.push(input);
      if (input === "/api/v1/territories/countries") {
        return new Response(
          JSON.stringify([
            { code: "RU", name: "Russia" },
            { code: "BY", name: "Belarus" },
          ]),
        );
      }
      if (input.startsWith("/api/v1/territories/regions")) {
        return new Response(
          JSON.stringify({
            error: {
              code: "TERRITORY_REFERENCE_UNAVAILABLE",
              message: "Not loaded",
            },
          }),
          { status: 503 },
        );
      }
      if (input.startsWith("/api/v1/investigations/scenarios?")) {
        return new Response(JSON.stringify([]));
      }
      if (input.startsWith("/api/v1/sources?")) {
        const country = input.includes("country=BY") ? "BY" : "RU";
        return new Response(
          JSON.stringify([
            {
              id: "open-meteo",
              country,
              kind: "WEATHER_FORECAST",
              mode: "LIVE",
              status: "EXPERIMENTAL",
            },
            ...(country === "RU"
              ? [
                  {
                    id: "saturn",
                    country,
                    kind: "TREATMENT_NOTICE",
                    mode: "LIVE",
                    status: "EXPERIMENTAL",
                  },
                ]
              : []),
          ]),
        );
      }
      return new Response(null, { status: 404 });
    }),
  );
  render(<App />);
  expect(
    await screen.findByRole("heading", {
      name: "Предварительные сведения по местности",
    }),
  ).toBeTruthy();
  expect(screen.queryByLabelText("Территория")).toBeNull();
  expect(
    screen.queryByRole("link", { name: "Перейти к реальным источникам" }),
  ).toBeNull();
  expect(
    screen.getByLabelText("Область / регион").hasAttribute("disabled"),
  ).toBe(true);
  expect(
    screen.queryByRole("button", { name: "Загрузить прогноз на 24 часа" }),
  ).toBeNull();
  expect(
    screen.queryByRole("button", { name: "Загрузить одну страницу" }),
  ).toBeNull();
  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "BY" },
  });
  expect(
    await screen.findByRole("heading", {
      name: "Предварительные сведения по местности",
    }),
  ).toBeTruthy();
  expect(
    calls.filter((url) => url === "/api/v1/sources/saturn/treatments"),
  ).toHaveLength(0);
});
