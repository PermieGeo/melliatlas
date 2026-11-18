import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { splitCoordinateSearch } from "../src/components/PlaceSearchToolbar";

const region = {
  id: "ru:region:smo",
  country: "RU",
  kind: "region",
  name: "Smolensk region",
  parent_id: null,
  reference_id: "reviewed-v1",
  valid_on: "2026-01-01",
  geometry_status: "available",
};

vi.mock("../src/components/MapPanel", () => ({
  MapPanel: ({
    draftPoint,
  }: {
    draftPoint: { latitude: number; longitude: number } | null;
  }) => (
    <output data-testid="map-draft-center">
      {draftPoint
        ? `${draftPoint.latitude},${draftPoint.longitude}`
        : "no draft"}
    </output>
  ),
}));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe("place-first workspace", () => {
  it("parses a coordinate pair without guessing ambiguous separators", () => {
    expect(splitCoordinateSearch("54.947, 31.080")).toEqual([
      "54.947",
      "31.080",
    ]);
    expect(splitCoordinateSearch("54,947; 31,080")).toEqual([
      "54,947",
      "31,080",
    ]);
    expect(splitCoordinateSearch("54,947,31,080")).toBeNull();
    expect(splitCoordinateSearch("54.947")).toBeNull();
  });

  it("places global and regional controls ahead of the map, verifies coordinates and keeps storage disabled", async () => {
    const calls: Array<{ path: string; body: string | null }> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: string, init?: RequestInit) => {
        calls.push({
          path: input,
          body: typeof init?.body === "string" ? init.body : null,
        });
        if (input === "/api/v1/territories/countries") {
          return new Response(JSON.stringify([{ code: "RU", name: "Russia" }]));
        }
        if (input.startsWith("/api/v1/territories/regions?")) {
          return new Response(JSON.stringify([region]));
        }
        if (input.startsWith("/api/v1/investigations/scenarios?")) {
          return new Response("[]");
        }
        if (input.startsWith("/api/v1/sources?")) {
          return new Response("[]");
        }
        if (input === "/api/v1/territories/resolve-point") {
          return new Response(
            JSON.stringify({ region_id: region.id, district_id: null }),
          );
        }
        return new Response(
          JSON.stringify({
            error: { code: "MISSING", message: "Not imported" },
          }),
          { status: 404 },
        );
      }),
    );

    const { container } = render(<App />);
    expect(container.querySelector("header.masthead #country")).toBeTruthy();
    expect(
      container.querySelector(".place-search-toolbar #reference-region"),
    ).toBeTruthy();
    expect(container.querySelector("main .map-section")).toBeTruthy();
    expect(
      container.querySelector("aside.context-column .area-draft-panel"),
    ).toBeTruthy();
    expect(
      container.querySelector("aside.context-column .controls"),
    ).toBeTruthy();
    expect(
      container.querySelector("aside.context-column .weather-panel"),
    ).toBeTruthy();
    expect(screen.getByText("Сохранённые места")).toBeTruthy();
    expect(
      screen.getByText(/Серверный API сохранения мест пока отключён/),
    ).toBeTruthy();
    expect(
      screen.getByText(/Запрос Сатурн запускается только кнопкой/),
    ).toBeTruthy();

    const search = screen.getByLabelText("Найти точку по координатам");
    expect(search.hasAttribute("disabled")).toBe(true);
    await waitFor(() =>
      expect(
        screen.getByLabelText("Область / регион").querySelectorAll("option")
          .length,
      ).toBe(2),
    );
    fireEvent.change(screen.getByLabelText("Область / регион"), {
      target: { value: region.id },
    });
    await waitFor(() => expect(search.hasAttribute("disabled")).toBe(false));
    fireEvent.change(search, { target: { value: "54.947, 31.080" } });
    fireEvent.click(screen.getByRole("button", { name: "Найти на карте" }));
    await waitFor(() =>
      expect(screen.getByTestId("map-draft-center").textContent).toBe(
        "54.947,31.08",
      ),
    );
    expect(
      screen.getByRole("button", { name: "Отменить черновик" }),
    ).toBeTruthy();
    const pointRead = calls.find(
      (item) => item.path === "/api/v1/territories/resolve-point",
    );
    expect(JSON.parse(pointRead?.body ?? "null")).toEqual({
      country: "RU",
      latitude: 54.947,
      longitude: 31.08,
    });
    expect(calls.some((item) => item.path.startsWith("/api/v1/places"))).toBe(
      false,
    );
    expect(new URL(window.location.href).search).toBe("");
  });
});
