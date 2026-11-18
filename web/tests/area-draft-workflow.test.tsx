import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useAreaDraft } from "../src/hooks/useAreaDraft";

const result = {
  coverage: "UNVERIFIED",
  south: 53.9,
  north: 54.1,
  longitude_ranges: [[31.9, 32.1]],
  nominal_area_km2: 225,
  districts: [
    {
      id: "ru:district:a",
      region_id: "ru:region:smo",
      name: "A",
      reference_id: "ref",
    },
  ],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("region-scoped unsaved area workflow", () => {
  it("requires a region and a map click before requesting districts", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(result)));
    vi.stubGlobal("fetch", fetchMock);
    const { result: state, rerender } = renderHook(
      ({ region }) => useAreaDraft("RU", region),
      { initialProps: { region: "" } },
    );
    act(() => state.current.start());
    expect(state.current.editing).toBe(false);
    rerender({ region: "ru:region:smo" });
    act(() => {
      state.current.start();
      state.current.selectPoint({ longitude: 32, latitude: 54 });
    });
    // A click after enabling draft mode is a separate user interaction.
    act(() => state.current.selectPoint({ longitude: 32, latitude: 54 }));
    expect(state.current.draft?.widthKm).toBe(15);
    expect(state.current.draft?.heightKm).toBe(15);
    expect(fetchMock).not.toHaveBeenCalled();
    await act(async () => {
      await state.current.checkDistricts();
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(state.current.preview?.districts).toHaveLength(1);
    expect(state.current.preview?.coverage).toBe("UNVERIFIED");
  });

  it("invalidates stale results after resizing and on region changes", async () => {
    let finish: ((response: Response) => void) | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(
        () =>
          new Promise<Response>((resolve) => {
            finish = resolve;
          }),
      ),
    );
    const { result: state, rerender } = renderHook(
      ({ region }) => useAreaDraft("RU", region),
      { initialProps: { region: "ru:region:smo" } },
    );
    act(() => state.current.start());
    act(() => state.current.selectPoint({ longitude: 32, latitude: 54 }));
    let pending: Promise<void> | undefined;
    act(() => {
      pending = state.current.checkDistricts();
    });
    expect(state.current.status).toBe("loading");
    act(() => state.current.resize("widthKm", 20));
    expect(state.current.preview).toBeNull();
    expect(state.current.status).toBe("idle");
    await act(async () => {
      finish?.(new Response(JSON.stringify(result)));
      await pending;
    });
    expect(state.current.preview).toBeNull();
    rerender({ region: "ru:region:other" });
    await waitFor(() => expect(state.current.draft).toBeNull());
    expect(state.current.editing).toBe(false);
  });

  it("preserves resized dimensions when the map moves an existing draft", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () => new Response(JSON.stringify(result)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result: state } = renderHook(() =>
      useAreaDraft("RU", "ru:region:smo"),
    );
    act(() => state.current.start());
    act(() => state.current.selectPoint({ latitude: 54, longitude: 32 }));
    act(() => state.current.resize("widthKm", 30));
    act(() => state.current.resize("heightKm", 25));
    await act(async () => state.current.checkDistricts());
    expect(state.current.preview).not.toBeNull();
    act(() => state.current.selectPoint({ latitude: 54.1, longitude: 32.25 }));
    expect(state.current.draft).toMatchObject({
      center: { latitude: 54.1, longitude: 32.25 },
      widthKm: 30,
      heightKm: 25,
    });
    expect(state.current.preview).toBeNull();
    expect(state.current.status).toBe("idle");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("keeps invalid dimensions unchanged and cancels a draft without persistence", () => {
    const { result: state } = renderHook(() =>
      useAreaDraft("RU", "ru:region:smo"),
    );
    act(() => state.current.start());
    act(() => state.current.selectPoint({ longitude: 32, latitude: 54 }));
    act(() => state.current.resize("heightKm", 31));
    expect(state.current.draft?.heightKm).toBe(15);
    act(() => state.current.resize("heightKm", 25));
    expect(state.current.draft?.heightKm).toBe(25);
    act(() => state.current.cancel());
    expect(state.current.draft).toBeNull();
    expect(state.current.editing).toBe(false);
  });
});

describe("verified coordinate entry", () => {
  it("does not send invalid inputs, and verifies selected region before moving a draft", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () =>
        new Response(
          JSON.stringify({ region_id: "ru:region:smo", district_id: null }),
        ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result: state } = renderHook(() =>
      useAreaDraft("RU", "ru:region:smo"),
    );
    act(() => state.current.start());
    await act(async () => state.current.selectCoordinates("bad", "32"));
    expect(state.current.coordinateStatus).toBe("invalid");
    expect(fetchMock).not.toHaveBeenCalled();
    await act(async () => state.current.selectCoordinates("54,1", "32.25"));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/api/v1/territories/resolve-point",
    );
    const request = fetchMock.mock.calls[0]?.[1];
    expect(request?.method).toBe("POST");
    expect(JSON.parse(String(request?.body))).toMatchObject({
      country: "RU",
      latitude: 54.1,
      longitude: 32.25,
    });
    expect(state.current.draft?.center).toEqual({
      latitude: 54.1,
      longitude: 32.25,
    });
    expect(state.current.coordinateFocus).toEqual({
      latitude: 54.1,
      longitude: 32.25,
    });
  });

  it("preserves dimensions for verified coordinate entry and rejects polar overflow before I/O", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () =>
        new Response(
          JSON.stringify({ region_id: "ru:region:smo", district_id: null }),
        ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result: state } = renderHook(() =>
      useAreaDraft("RU", "ru:region:smo"),
    );
    act(() => state.current.start());
    act(() => state.current.selectPoint({ latitude: 54, longitude: 32 }));
    act(() => state.current.resize("heightKm", 30));
    act(() => state.current.resize("widthKm", 20));
    expect(state.current.selectPoint({ latitude: 89.9, longitude: 32 })).toBe(
      false,
    );
    await act(async () => state.current.selectCoordinates("89.9", "32"));
    expect(state.current.coordinateStatus).toBe("invalid");
    expect(fetchMock).not.toHaveBeenCalled();
    await act(async () => state.current.selectCoordinates("54.2", "32.1"));
    expect(state.current.draft).toMatchObject({
      center: { latitude: 54.2, longitude: 32.1 },
      widthKm: 20,
      heightKm: 30,
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("rejects a point in a different region, keeping an existing draft unchanged", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>(
        async () =>
          new Response(
            JSON.stringify({ region_id: "ru:region:other", district_id: null }),
          ),
      ),
    );
    const { result: state } = renderHook(() =>
      useAreaDraft("RU", "ru:region:smo"),
    );
    act(() => state.current.start());
    act(() => state.current.selectPoint({ latitude: 54, longitude: 32 }));
    await act(async () => state.current.selectCoordinates("55", "35"));
    expect(state.current.coordinateStatus).toBe("outside");
    expect(state.current.draft?.center).toEqual({
      latitude: 54,
      longitude: 32,
    });
  });

  it("does not apply a late coordinate response after cancel or region switch", async () => {
    let finish: ((response: Response) => void) | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>(
        () =>
          new Promise<Response>((resolve) => {
            finish = resolve;
          }),
      ),
    );
    const { result: state, rerender } = renderHook(
      ({ region }) => useAreaDraft("RU", region),
      { initialProps: { region: "ru:region:smo" } },
    );
    act(() => state.current.start());
    let pending: Promise<void> | undefined;
    act(() => {
      pending = state.current.selectCoordinates("54", "32");
    });
    expect(state.current.coordinateStatus).toBe("checking");
    rerender({ region: "ru:region:other" });
    await act(async () => {
      finish?.(
        new Response(
          JSON.stringify({ region_id: "ru:region:smo", district_id: null }),
        ),
      );
      await pending;
    });
    expect(state.current.draft).toBeNull();
    expect(state.current.coordinateFocus).toBeNull();
    expect(state.current.coordinateStatus).toBe("idle");
  });
});
