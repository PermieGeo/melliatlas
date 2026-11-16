import { useEffect, useRef, useState } from "react";
import { listExternalSources, readWeatherForecast } from "../api/client";
import type { CountryCode, Position, WeatherForecast } from "../api/types";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

/** Weather is point-scoped and never treated as a confirmed chemical-exposure forecast. */
interface Props {
  country: CountryCode;
  locale: Locale;
  point: Position | null;
}

/** A manual read with cancellation and no browser storage, retry loop or automatic polling. */
export function WeatherPanel({ country, locale, point }: Props) {
  const [available, setAvailable] = useState("");
  const [forecast, setForecast] = useState<WeatherForecast | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const readController = useRef<AbortController | null>(null);
  const tr = (key: TranslationKey, values?: Record<string, string | number>) =>
    t(locale, key, values);

  useEffect(() => {
    const controller = new AbortController();
    setAvailable("");
    if (country) {
      void listExternalSources(country, controller.signal).then((response) => {
        if (controller.signal.aborted) return;
        setAvailable(
          response.kind === "ok" &&
            response.data.some(
              (source) =>
                source.id === "open-meteo" && source.country === country,
            )
            ? country
            : "",
        );
      });
    }
    return () => controller.abort();
  }, [country]);

  useEffect(() => {
    readController.current?.abort();
    setForecast(null);
    setBusy(false);
    setError("");
    return () => readController.current?.abort();
  }, [country, point?.latitude, point?.longitude]);

  if (available !== country || !country) return null;

  const read = () => {
    if (!point || busy) return;
    readController.current?.abort();
    const controller = new AbortController();
    readController.current = controller;
    setBusy(true);
    setError("");
    setForecast(null);
    void readWeatherForecast(point, controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      setBusy(false);
      if (response.kind === "error") {
        setError(response.code);
        return;
      }
      if (
        response.data.requested_latitude !== point.latitude ||
        response.data.requested_longitude !== point.longitude
      ) {
        setError("INVALID_RESPONSE");
        return;
      }
      setForecast(response.data);
    });
  };
  const number = (value: number | null) =>
    value === null
      ? tr("weatherMissing")
      : new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(
          value,
        );
  return (
    <section className="weather-panel" aria-label={tr("weatherTitle")}>
      <h2>{tr("weatherTitle")}</h2>
      <p className="warning-text">{tr("weatherWarning")}</p>
      <p className="field-help">{tr("weatherHelp")}</p>
      <button type="button" disabled={!point || busy} onClick={read}>
        {busy ? tr("weatherLoading") : tr("weatherRead")}
      </button>
      {error && (
        <p role="alert" className="warning-text">
          {tr("weatherError", { reason: error })}
        </p>
      )}
      {forecast && (
        <div role="status">
          <p className="muted">
            {tr("weatherGrid", {
              lat: forecast.grid_latitude,
              lon: forecast.grid_longitude,
              time: forecast.captured_at,
            })}
          </p>
          <div className="weather-scroll">
            <table className="weather-table">
              <thead>
                <tr>
                  <th>{tr("weatherTime")}</th>
                  <th>{tr("weatherWind")}</th>
                  <th>{tr("weatherDirection")}</th>
                  <th>{tr("weatherGusts")}</th>
                  <th>{tr("weatherRain")}</th>
                </tr>
              </thead>
              <tbody>
                {forecast.hours.map((hour) => (
                  <tr key={hour.time}>
                    <td>{hour.time.replace("T", " ").slice(0, 16)}</td>
                    <td>{number(hour.wind_speed_kmh)}</td>
                    <td>{number(hour.wind_direction_degrees)}</td>
                    <td>{number(hour.wind_gusts_kmh)}</td>
                    <td>{number(hour.precipitation_mm)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {forecast.uncertainties.map((note) => (
            <p className="warning-text" key={note}>
              {note}
            </p>
          ))}
          <a
            href={forecast.source_uri}
            target="_blank"
            rel="noopener noreferrer"
          >
            {tr("weatherAttribution")}
          </a>
        </div>
      )}
    </section>
  );
}
