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
  expect(screen.getByText(/Только вымышленные данные/)).toBeTruthy();
  expect(
    await screen.findByText(/Границы и перечень регионов пока не загружены/),
  ).toBeTruthy();
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

it("reopens a completed result and shows a distinct missing-ID error", async () => {
  const calls = mockApi();
  render(<App />);
  fireEvent.change(screen.getByLabelText("Открыть по ID"), {
    target: { value: fixture.id },
  });
  fireEvent.click(screen.getByRole("button", { name: "Открыть" }));
  expect(
    await screen.findByText(/Предварительный план сформирован/),
  ).toBeTruthy();
  expect(calls.some((entry) => entry.path.endsWith(fixture.id))).toBe(true);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) =>
      input.startsWith("/api/v1/investigations/")
        ? new Response(
            JSON.stringify({
              error: { code: "INVESTIGATION_NOT_FOUND", message: "not found" },
            }),
            { status: 404 },
          )
        : new Response(JSON.stringify([])),
    ),
  );
  fireEvent.click(screen.getByRole("button", { name: "Открыть" }));
  expect(
    await screen.findByText(/Результат в памяти сервера мог исчезнуть/),
  ).toBeTruthy();
});

it("disables an unsupported BY demonstration and ignores a stale result after country switch", async () => {
  mockApi();
  render(<App />);
  fireEvent.change(screen.getByLabelText("Страна"), {
    target: { value: "BY" },
  });
  expect(
    (
      screen.getByRole("button", {
        name: /Исследовать размещение/,
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
  await waitFor(() => expect(screen.getByLabelText("Территория")).toBeTruthy());
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
      if (input === "/api/v1/investigations") {
        return new Promise<Response>((resolve) => {
          pending.resolve = resolve;
        });
      }
      return new Response(JSON.stringify(fixture));
    }),
  );
  render(<App />);
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
  expect(
    (
      screen.getByRole("button", {
        name: /Исследовать размещение/,
      }) as HTMLButtonElement
    ).disabled,
  ).toBe(true);
});

it("distinguishes completed insufficient evidence from a backend failure", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input === "/api/v1/territories/countries")
        return new Response(JSON.stringify([{ code: "RU", name: "Russia" }]));
      if (input.startsWith("/api/v1/territories/regions"))
        return new Response(JSON.stringify([]));
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
  fireEvent.click(
    screen.getByRole("button", { name: /Исследовать размещение/ }),
  );
  expect(
    await screen.findByText(/недостаточно проверенных стоянок/),
  ).toBeTruthy();
  expect(screen.queryByText(/Предварительный план сформирован/)).toBeNull();
});
