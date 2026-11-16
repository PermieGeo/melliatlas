import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { WeatherPanel } from "../src/components/WeatherPanel";
import {
  decodeSources,
  decodeWeatherForecast,
  WireError,
} from "../src/api/validation";

const weatherSource = [
  {
    id: "open-meteo",
    country: "BY",
    kind: "WEATHER_FORECAST",
    mode: "LIVE",
    status: "EXPERIMENTAL",
  },
];
const hours = Array.from({ length: 24 }, (_, index) => ({
  time: new Date(Date.UTC(2026, 10, 15, index)).toISOString(),
  wind_speed_kmh: 10,
  wind_direction_degrees: 220,
  wind_gusts_kmh: 14,
  precipitation_mm: index === 0 ? null : 0,
}));
const forecast = {
  source_id: "open-meteo:forecast",
  source_uri: "https://open-meteo.com/en/docs",
  source_mode: "LIVE",
  synthetic: false,
  captured_at: "2026-11-15T12:00:00Z",
  requested_latitude: 54,
  requested_longitude: 32,
  grid_latitude: 54.02,
  grid_longitude: 32.03,
  hours,
  uncertainties: ["Model forecast, not measured pesticide drift"],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Weather forecast boundary", () => {
  it("accepts nullable measurements but rejects fabricated or mismatched evidence", () => {
    expect(decodeSources(weatherSource)[0]?.id).toBe("open-meteo");
    expect(() =>
      decodeSources([{ ...weatherSource[0], kind: "TREATMENT_NOTICE" }]),
    ).toThrow(WireError);
    expect(
      decodeWeatherForecast(forecast).hours[0]?.precipitation_mm,
    ).toBeNull();
    expect(() =>
      decodeWeatherForecast({ ...forecast, synthetic: true }),
    ).toThrow(WireError);
    expect(() =>
      decodeWeatherForecast({ ...forecast, source_uri: "javascript:alert(1)" }),
    ).toThrow(WireError);
    expect(() =>
      decodeWeatherForecast({
        ...forecast,
        source_uri: "https://open-meteo.com.evil.invalid/docs",
      }),
    ).toThrow(WireError);
    expect(() =>
      decodeWeatherForecast({ ...forecast, hours: hours.slice(1) }),
    ).toThrow(WireError);
    const skippedHour = hours.map((hour, index) =>
      index === 5
        ? { ...hour, time: new Date(Date.UTC(2026, 10, 15, 6)).toISOString() }
        : hour,
    );
    expect(() =>
      decodeWeatherForecast({ ...forecast, hours: skippedHour }),
    ).toThrow(WireError);
    expect(() =>
      decodeWeatherForecast({
        ...forecast,
        hours: [{ ...hours[0], wind_direction_degrees: -1 }, ...hours.slice(1)],
      }),
    ).toThrow(WireError);
  });

  it("automatically reads a validated territory point inline and displays attribution", async () => {
    const fetchMock = vi.fn(async (path: string, options?: RequestInit) => {
      if (path.startsWith("/api/v1/sources?"))
        return new Response(JSON.stringify(weatherSource));
      expect(path).toBe("/api/v1/sources/weather/forecast");
      expect(options?.method).toBe("POST");
      expect(JSON.parse(String(options?.body))).toEqual({
        latitude: 54,
        longitude: 32,
      });
      return new Response(JSON.stringify(forecast));
    });
    vi.stubGlobal("fetch", fetchMock);
    const view = render(<WeatherPanel country="BY" locale="en" point={null} />);
    await screen.findByText("Weather forecast · Open-Meteo");
    expect(
      screen.getByText(/Select a territory with a validated boundary/),
    ).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    view.rerender(
      <WeatherPanel
        country="BY"
        locale="en"
        point={{ latitude: 54, longitude: 32 }}
      />,
    );
    await screen.findByText(/Forecast grid: 54.02, 32.03/);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(
      screen
        .getByRole("link", { name: /Weather data by Open-Meteo/ })
        .getAttribute("href"),
    ).toBe("https://open-meteo.com/en/docs");
    expect(screen.getByText("n/a")).toBeDefined();
    view.rerender(
      <WeatherPanel
        country="RU"
        locale="en"
        point={{ latitude: 54, longitude: 32 }}
      />,
    );
    await waitFor(() => expect(screen.queryByText(/Forecast grid/)).toBeNull());
  });

  it("does not display weather when the backend does not advertise it", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify([])));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <WeatherPanel
        country="RU"
        locale="en"
        point={{ latitude: 54, longitude: 32 }}
      />,
    );
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(
      screen.getByText("The weather provider is disabled or unavailable."),
    ).toBeTruthy();
  });
});
