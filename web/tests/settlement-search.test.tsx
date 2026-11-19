import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  PlaceSearchToolbar,
  splitCoordinateSearch,
} from "../src/components/PlaceSearchToolbar";
import { FieldHelp } from "../src/components/FieldHelp";
import type { TerritoryNavigation } from "../src/hooks/useTerritoryReference";

const navigation: TerritoryNavigation = {
  regionId: "ru:region:smo",
  districts: [],
  districtId: "",
  districtMessage: "referenceDistrictEmpty",
  geometryMessage: "referenceGeometryMissing",
  geometry: null,
  selectRegion: vi.fn(),
  selectDistrict: vi.fn(),
  selectByPoint: vi.fn(),
  retryDistricts: vi.fn(),
};

function renderSearch(onCoordinates = vi.fn()) {
  return render(
    <PlaceSearchToolbar
      country="RU"
      locale="ru"
      regions={[]}
      navigation={navigation}
      catalogMessage="availableRegions"
      onRetryRegions={vi.fn()}
      coordinateStatus="idle"
      onCoordinatesEdited={vi.fn()}
      onCoordinates={onCoordinates}
    />,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("searches names on submit and validates picked coordinates through the existing caller", async () => {
  const request = vi.fn(async (_path: string, init?: RequestInit) => {
    expect(init?.method).toBe("POST");
    expect(JSON.parse(String(init?.body))).toEqual({
      country: "RU",
      query: "Смоленск",
      language: "ru",
    });
    return new Response(
      JSON.stringify([
        {
          id: 1,
          name: "Смоленск",
          country: "RU",
          admin1: "Smolensk",
          latitude: 54.78,
          longitude: 32.04,
          source_uri: "https://open-meteo.com/en/docs/geocoding-api",
        },
      ]),
    );
  });
  vi.stubGlobal("fetch", request);
  const onCoordinates = vi.fn();
  renderSearch(onCoordinates);
  fireEvent.change(screen.getByRole("textbox", { name: "Поиск" }), {
    target: { value: "Смоленск" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Найти на карте" }));
  const result = await screen.findByRole("button", { name: /Смоленск/ });
  expect(request).toHaveBeenCalledOnce();
  fireEvent.click(result);
  expect(onCoordinates).toHaveBeenCalledWith("54.78", "32.04");
});

it("handles coordinates locally and reports source outages without fictional fallbacks", async () => {
  const fetcher = vi.fn(
    async () =>
      new Response(
        JSON.stringify({
          error: { code: "SOURCE_READ_FAILED", message: "unavailable" },
        }),
        { status: 502 },
      ),
  );
  vi.stubGlobal("fetch", fetcher);
  const onCoordinates = vi.fn();
  renderSearch(onCoordinates);
  const textbox = screen.getByRole("textbox", { name: "Поиск" });
  fireEvent.change(textbox, { target: { value: "54,947; 31,080" } });
  fireEvent.click(screen.getByRole("button", { name: "Найти на карте" }));
  expect(onCoordinates).toHaveBeenCalledWith("54,947", "31,080");
  expect(fetcher).not.toHaveBeenCalled();
  fireEvent.change(textbox, { target: { value: "Смоленск" } });
  fireEvent.click(screen.getByRole("button", { name: "Найти на карте" }));
  await waitFor(() =>
    expect(screen.getByRole("alert").textContent).toMatch(/недоступен/),
  );
  expect(screen.queryByRole("button", { name: /Демо/ })).toBeNull();
  expect(splitCoordinateSearch("54,947,31,080")).toBeNull();
});

it("shows contextual guidance on focus and Escape hides it", () => {
  render(
    <FieldHelp
      locale="ru"
      label="workspaceCoordinateSearch"
      explanation="workspaceSearchNote"
    />,
  );
  const help = screen.getByRole("button", { name: "Подсказка: Поиск" });
  expect(screen.queryByRole("tooltip")).toBeNull();
  fireEvent.focus(help);
  expect(screen.getByRole("tooltip").textContent).toMatch(/населённого пункта/);
  fireEvent.keyDown(help, { key: "Escape" });
  expect(screen.queryByRole("tooltip")).toBeNull();
});
