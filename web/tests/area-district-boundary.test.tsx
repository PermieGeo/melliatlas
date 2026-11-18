import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AreaDistrictResult } from "../src/api/types";
import { useAreaDistrictBoundary } from "../src/hooks/useAreaDistrictBoundary";

const preview: AreaDistrictResult = {
  coverage: "UNVERIFIED",
  south: 53.9,
  north: 54.1,
  longitude_ranges: [[31.9, 32.1]],
  nominal_area_km2: 225,
  districts: [
    {
      id: "ru:district:one",
      region_id: "ru:region:smo",
      name: "District one",
      reference_id: "reviewed-v1",
    },
    {
      id: "ru:district:two",
      region_id: "ru:region:smo",
      name: "District two",
      reference_id: "reviewed-v1",
    },
  ],
};

function geometry(territoryId: string, referenceId = "reviewed-v1") {
  return {
    territory_id: territoryId,
    reference_id: referenceId,
    coordinate_system: "EPSG:4326",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [32, 54],
          [32.2, 54],
          [32.2, 54.2],
          [32, 54.2],
          [32, 54],
        ],
      ],
    },
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("on-demand district boundary inspection", () => {
  it("requests only the selected public district and toggles the map outline", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () => new Response(JSON.stringify(geometry("ru:district:one"))),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAreaDistrictBoundary(preview));

    await act(async () => result.current.select("ru:district:one"));
    expect(result.current.status).toBe("ready");
    expect(result.current.geometry?.territory_id).toBe("ru:district:one");
    expect(result.current.districtId).toBe("ru:district:one");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const url = fetchMock.mock.calls[0]?.[0];
    const request = fetchMock.mock.calls[0]?.[1];
    expect(url).toBe("/api/v1/territories/geometry/ru%3Adistrict%3Aone");
    expect(url).not.toContain("latitude");
    expect(url).not.toContain("32");
    expect(request?.method).toBeUndefined();

    await act(async () => result.current.select("ru:district:one"));
    expect(result.current.geometry).toBeNull();
    expect(result.current.status).toBe("idle");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("rejects a mismatched reference or district ID without drawing it", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () => new Response(JSON.stringify(geometry("ru:district:other"))),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAreaDistrictBoundary(preview));

    await act(async () => result.current.select("ru:district:one"));
    expect(result.current.status).toBe("failed");
    expect(result.current.errorCode).toBe("INVALID_RESPONSE");
    expect(result.current.geometry).toBeNull();

    fetchMock.mockImplementation(
      async () =>
        new Response(JSON.stringify(geometry("ru:district:one", "stale-ref"))),
    );
    await act(async () => result.current.select("ru:district:two"));
    expect(result.current.errorCode).toBe("INVALID_RESPONSE");
    expect(result.current.geometry).toBeNull();
  });

  it("aborts a previous request when another district is selected", async () => {
    let finishFirst: ((response: Response) => void) | undefined;
    let firstSignal: AbortSignal | undefined;
    const fetchMock = vi.fn<typeof fetch>((url, init) => {
      expect(String(url)).toContain("/api/v1/territories/geometry/");
      if (!firstSignal) {
        firstSignal = init?.signal ?? undefined;
        return new Promise<Response>((resolve) => {
          finishFirst = resolve;
        });
      }
      return Promise.resolve(
        new Response(JSON.stringify(geometry("ru:district:two"))),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAreaDistrictBoundary(preview));

    let pending: Promise<void> | undefined;
    act(() => {
      pending = result.current.select("ru:district:one");
    });
    expect(result.current.status).toBe("loading");
    await act(async () => result.current.select("ru:district:two"));
    expect(firstSignal?.aborted).toBe(true);
    expect(result.current.geometry?.territory_id).toBe("ru:district:two");

    await act(async () => {
      finishFirst?.(new Response(JSON.stringify(geometry("ru:district:one"))));
      await pending;
    });
    expect(result.current.geometry?.territory_id).toBe("ru:district:two");
  });

  it("removes stale selections after the intersection preview changes", async () => {
    let finish: ((response: Response) => void) | undefined;
    const fetchMock = vi.fn<typeof fetch>(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result, rerender } = renderHook(
      ({ current }) => useAreaDistrictBoundary(current),
      { initialProps: { current: preview as AreaDistrictResult | null } },
    );
    let pending: Promise<void> | undefined;
    act(() => {
      pending = result.current.select("ru:district:one");
    });
    rerender({ current: { ...preview, nominal_area_km2: 300 } });
    await waitFor(() => expect(result.current.districtId).toBeNull());
    await act(async () => {
      finish?.(new Response(JSON.stringify(geometry("ru:district:one"))));
      await pending;
    });
    expect(result.current.geometry).toBeNull();
    expect(result.current.status).toBe("idle");
    rerender({ current: null });
    expect(result.current.geometry).toBeNull();
  });

  it("reports unavailable geometry and ignores IDs outside the result", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () =>
        new Response(
          JSON.stringify({
            error: { code: "TERRITORY_GEOMETRY_MISSING", message: "Missing" },
          }),
          { status: 404 },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAreaDistrictBoundary(preview));
    await act(async () => result.current.select("ru:district:not-listed"));
    expect(fetchMock).not.toHaveBeenCalled();
    await act(async () => result.current.select("ru:district:one"));
    expect(result.current.status).toBe("failed");
    expect(result.current.errorCode).toBe("TERRITORY_GEOMETRY_MISSING");
    expect(result.current.geometry).toBeNull();
  });
});
