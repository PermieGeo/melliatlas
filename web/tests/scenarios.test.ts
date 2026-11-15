import { afterEach, describe, expect, it, vi } from "vitest";
import { listScenarios } from "../src/api/client";
import {
  decodeCountries,
  decodeScenarios,
  WireError,
} from "../src/api/validation";

const scenario = {
  id: "fictional-2030-sample",
  name: "Sample fictional analysis",
  country: "PL",
  territory_id: "pl:region:sample",
  territory_name: "Sample territory (fictional)",
  source_mode: "SYNTHETIC",
  season_start: "2030-06-01",
  season_end: "2030-09-15",
  is_default: true,
};

afterEach(() => vi.unstubAllGlobals());

describe("dynamic country and scenario contracts", () => {
  it("accepts countries supplied by the API without a browser-side country enum", () => {
    expect(decodeCountries([{ code: "PL", name: "Poland" }])[0]?.code).toBe(
      "PL",
    );
    expect(() =>
      decodeCountries([{ code: "not-a-code", name: "Invalid" }]),
    ).toThrow(WireError);
  });

  it("validates advertised seasons, identity and source mode", () => {
    expect(decodeScenarios([scenario])[0]?.season_start).toBe("2030-06-01");
    expect(() =>
      decodeScenarios([{ ...scenario, season_start: "2030-02-30" }]),
    ).toThrow(WireError);
    expect(() =>
      decodeScenarios([{ ...scenario, season_end: "2030-01-01" }]),
    ).toThrow(WireError);
    expect(() =>
      decodeScenarios([{ ...scenario, source_mode: "UNVERIFIED_LIVE" }]),
    ).toThrow(WireError);
    expect(() => decodeScenarios([scenario, scenario])).toThrow(WireError);
  });

  it("does not assume an executable scenario for every listed country", async () => {
    const fetchMock = vi.fn(async (path: string) => {
      expect(path).toBe("/api/v1/investigations/scenarios?country=PL");
      return new Response(JSON.stringify([]));
    });
    vi.stubGlobal("fetch", fetchMock);
    expect(await listScenarios("PL", new AbortController().signal)).toEqual({
      kind: "ok",
      data: [],
    });
  });
});
