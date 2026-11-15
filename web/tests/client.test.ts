import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getInvestigation,
  listCountries,
  listRegions,
  startInvestigation,
} from "../src/api/client";
import { decodeInvestigation, WireError } from "../src/api/validation";
import fixture from "./fixtures/combined.json";

afterEach(() => vi.unstubAllGlobals());

describe("FastAPI response boundary", () => {
  it("decodes the actual combined synthetic response and rejects private point echoes", () => {
    const result = decodeInvestigation(fixture);
    expect(result.status).toBe("COMPLETED");
    expect(result.plan?.stops).toHaveLength(3);
    expect(
      result.replanning?.decisions.some(
        (entry) => entry.kind === "ECOLOGY_CHECK",
      ),
    ).toBe(true);
    expect(result.treatment_review?.screenings.length).toBeGreaterThan(0);
    expect(() =>
      decodeInvestigation({
        ...fixture,
        request: {
          ...fixture.request,
          starting_point: { longitude: 32, latitude: 54 },
        },
      }),
    ).toThrow(WireError);
  });

  it("rejects invalid nested treatment observations instead of trusting arbitrary JSON", () => {
    const review = fixture.treatment_review;
    expect(review).not.toBeNull();
    if (review === null) throw new Error("Missing fixture review");
    const broken = {
      ...fixture,
      treatment_review: {
        ...review,
        screenings: review.screenings.map((entry, index) =>
          index === 0 ? { ...entry, proximity: "SAFE" } : entry,
        ),
      },
    };
    expect(() => decodeInvestigation(broken)).toThrow(WireError);
  });

  it("submits the optional private coordinate only in the POST body", async () => {
    const fetchMock = vi.fn(async (path: string, options?: RequestInit) => {
      expect(path).toBe("/api/v1/investigations");
      expect(options?.method).toBe("POST");
      return new Response(JSON.stringify(fixture), { status: 202 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const response = await startInvestigation(
      {
        country: "RU",
        territory_id: "ru:region:smolensk",
        scenario_id: "synthetic-ru-2026-v04-ecology-treatment",
        season_start: "2026-05-01",
        season_end: "2026-08-15",
        starting_point: { longitude: 32.1, latitude: 54.2 },
      },
      new AbortController().signal,
    );
    expect(response.kind).toBe("ok");
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/investigations");
    const options = fetchMock.mock.calls[0]?.[1];
    expect(options?.method).toBe("POST");
    expect(options?.body).toContain('"longitude":32.1');
  });

  it("reports typed HTTP errors and rejects malformed success responses", async () => {
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
    const unavailable = await listRegions("BY", new AbortController().signal);
    expect(unavailable).toMatchObject({
      kind: "error",
      status: 503,
      code: "TERRITORY_REFERENCE_UNAVAILABLE",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () => new Response(JSON.stringify({ id: 99 }), { status: 200 }),
      ),
    );
    const invalid = await getInvestigation(
      fixture.id,
      new AbortController().signal,
    );
    expect(invalid).toMatchObject({ kind: "error", code: "INVALID_RESPONSE" });
  });

  it("reads countries and handles cancellation without turning it into an HTTP failure", async () => {
    const fetchMock = vi.fn(async (_path: string, options: RequestInit) => {
      if (options.signal?.aborted)
        throw new DOMException("Aborted", "AbortError");
      return new Response(
        JSON.stringify([
          { code: "RU", name: "Russia" },
          { code: "BY", name: "Belarus" },
        ]),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    const ready = await listCountries(new AbortController().signal);
    expect(ready.kind).toBe("ok");
    const controller = new AbortController();
    controller.abort();
    const aborted = await listCountries(controller.signal);
    expect(aborted).toMatchObject({
      kind: "error",
      code: "ABORTED",
      status: null,
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("classifies an in-flight DOMException abort across error realms", async () => {
    const fetchMock = vi.fn(
      (_path: string, options: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          options.signal?.addEventListener(
            "abort",
            () => reject(new DOMException("Aborted", "AbortError")),
            { once: true },
          );
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const controller = new AbortController();
    const pending = listCountries(controller.signal);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    controller.abort();
    expect(await pending).toMatchObject({
      kind: "error",
      code: "ABORTED",
      status: null,
    });
  });

  it("does not mistake response-body cancellation for invalid JSON", async () => {
    const controller = new AbortController();
    const response = new Response("{}");
    vi.spyOn(response, "json").mockImplementation(async () => {
      controller.abort();
      throw new DOMException("Aborted", "AbortError");
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => response),
    );
    expect(await listCountries(controller.signal)).toMatchObject({
      kind: "error",
      code: "ABORTED",
      status: null,
    });
  });
});
