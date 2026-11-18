import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { SaturnPanel } from "../src/components/SaturnPanel";
import {
  decodeSaturnPage,
  decodeSources,
  WireError,
} from "../src/api/validation";

const liveSource = [
  {
    id: "saturn",
    country: "RU",
    kind: "TREATMENT_NOTICE",
    mode: "LIVE",
    status: "EXPERIMENTAL",
  },
];

const livePage = {
  source_id: "saturn:public-beekeeper-portal",
  country: "RU",
  region_code: 55,
  region_id: "ru:region:smo",
  captured_at: "2026-11-15T17:00:00Z",
  page_number: 0,
  next_page: null,
  total_elements: 1,
  unidentified_records: 0,
  coverage_complete: false,
  record_limit_exceeded: false,
  notices: [
    {
      record_id: "71",
      plan_id: "17",
      country: "RU",
      source_id: "saturn:public-beekeeper-portal",
      source_uri: "https://bee.fgis-saturn.ru/",
      source_mode: "LIVE",
      synthetic: false,
      captured_at: "2026-11-15T17:00:00Z",
      published_at: null,
      scheduled_start: "2026-11-18T00:00:00Z",
      scheduled_end: "2026-11-19T00:00:00Z",
      revised: false,
      cadastral_number: null,
      geometry: null,
      products: [
        { name: "Reported product", crop: null, reported_bee_hazard_class: 2 },
      ],
      uncertainties: [
        "Unverified public notice; actual pesticide application is not established",
      ],
    },
  ],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Saturn live capability boundary", () => {
  it("strictly rejects synthetic or cross-country claims in a live payload", () => {
    expect(decodeSources(liveSource)[0]?.country).toBe("RU");
    expect(decodeSaturnPage(livePage).notices[0]?.synthetic).toBe(false);
    expect(() =>
      decodeSaturnPage({ ...livePage, record_limit_exceeded: "yes" }),
    ).toThrow(WireError);
    expect(() => decodeSaturnPage({ ...livePage, page_number: 10 })).toThrow(
      WireError,
    );
    expect(() => decodeSaturnPage({ ...livePage, next_page: 10 })).toThrow(
      WireError,
    );
    expect(() =>
      decodeSaturnPage({
        ...livePage,
        notices: [{ ...livePage.notices[0], synthetic: true }],
      }),
    ).toThrow(WireError);
    expect(() =>
      decodeSaturnPage({
        ...livePage,
        notices: [{ ...livePage.notices[0], country: "BY" }],
      }),
    ).toThrow(WireError);
  });

  it("only requests a live page after the source is advertised and the user clicks", async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.startsWith("/api/v1/sources?"))
        return new Response(JSON.stringify(liveSource));
      expect(url).toBe("/api/v1/sources/saturn/treatments");
      expect(init?.method).toBe("POST");
      expect(JSON.parse(String(init?.body))).toEqual({
        country: "RU",
        region_id: "ru:region:smo",
        page_number: 0,
      });
      return new Response(JSON.stringify(livePage));
    });
    vi.stubGlobal("fetch", fetchMock);
    const onNotices = vi.fn();
    render(
      <SaturnPanel
        country="RU"
        locale="en"
        regionId="ru:region:smo"
        onNotices={onNotices}
      />,
    );
    await screen.findByText("Saturn: public treatment notices");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Read one live page" }));
    await screen.findByText(/Field record 71/);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(onNotices).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ record_id: "71", synthetic: false }),
      ]),
    );
  });

  it("requires a canonical region instead of a typed Saturn subject code", async () => {
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify(liveSource)),
    );
    vi.stubGlobal("fetch", fetchMock);
    const onNotices = vi.fn();
    render(
      <SaturnPanel
        country="RU"
        locale="en"
        regionId=""
        onNotices={onNotices}
      />,
    );
    await screen.findByText(
      "Select an imported Russian region and a source-mapped district above before loading Saturn notices.",
    );
    expect(
      screen.getByRole("button", { name: "Read one live page" }),
    ).toHaveProperty("disabled", true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("never shows or requests Saturn for an unsupported country", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify([])));
    vi.stubGlobal("fetch", fetchMock);
    const onNotices = vi.fn();
    render(
      <SaturnPanel
        country="BY"
        locale="en"
        regionId="by:region:vi"
        onNotices={onNotices}
      />,
    );
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(screen.queryByText("Saturn: public treatment notices")).toBeNull();
    expect(fetchMock.mock.calls).toHaveLength(1);
    expect(onNotices).toHaveBeenCalledWith([]);
  });
});
