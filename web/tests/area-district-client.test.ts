import { afterEach, describe, expect, it, vi } from "vitest";
import { lookupIntersectingDistricts } from "../src/api/client";
import { decodeAreaDistrictResult, WireError } from "../src/api/validation";

const response = {
  coverage: "UNVERIFIED",
  south: 53.9,
  north: 54.1,
  longitude_ranges: [[31.9, 32.1]],
  nominal_area_km2: 225,
  districts: [
    {
      id: "ru:district:a",
      region_id: "ru:region:smo",
      name: "District A",
      reference_id: "ref",
    },
  ],
};

const draft = {
  country: "RU",
  regionId: "ru:region:smo",
  center: { longitude: 32, latitude: 54 },
  widthKm: 15,
  heightKm: 15,
};

afterEach(() => vi.unstubAllGlobals());

describe("read-only area district client", () => {
  it("sends the private center only in a POST body and parses coverage", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async () => new Response(JSON.stringify(response)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const result = await lookupIntersectingDistricts(
      draft,
      new AbortController().signal,
    );
    expect(result.kind).toBe("ok");
    if (result.kind !== "ok") throw new Error("Expected area response");
    expect(result.data.coverage).toBe("UNVERIFIED");
    expect(result.data.districts[0]?.id).toBe("ru:district:a");
    const path = fetchMock.mock.calls[0]?.[0];
    const init = fetchMock.mock.calls[0]?.[1];
    expect(path).toBe("/api/v1/territories/intersecting-districts");
    expect(init?.method).toBe("POST");
    expect(String(init?.body)).toContain('"longitude":32');
    expect(path).not.toContain("32");
  });

  it("rejects malformed bounds, coverage and duplicate district IDs", () => {
    expect(() =>
      decodeAreaDistrictResult({ ...response, coverage: "COMPLETE" }),
    ).toThrow(WireError);
    expect(() =>
      decodeAreaDistrictResult({ ...response, longitude_ranges: [[-181, 32]] }),
    ).toThrow(WireError);
    expect(() =>
      decodeAreaDistrictResult({
        ...response,
        districts: [response.districts[0], response.districts[0]],
      }),
    ).toThrow(WireError);
  });

  it("preserves unavailable reference failures without pretending there are zero districts", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              error: {
                code: "TERRITORY_REFERENCE_UNAVAILABLE",
                message: "No reference",
              },
            }),
            { status: 503 },
          ),
      ),
    );
    const result = await lookupIntersectingDistricts(
      draft,
      new AbortController().signal,
    );
    expect(result.kind).toBe("error");
    if (result.kind === "error")
      expect(result.code).toBe("TERRITORY_REFERENCE_UNAVAILABLE");
  });
});
