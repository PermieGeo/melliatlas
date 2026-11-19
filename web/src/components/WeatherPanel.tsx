import { useEffect, useState } from "react";
import { listExternalSources, readWeatherForecast } from "../api/client";
import type { CountryCode, Position, WeatherForecast } from "../api/types";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";
import { FieldHelp } from "./FieldHelp";

interface Props {
  country: CountryCode;
  locale: Locale;
  point: Position | null;
  refreshToken?: number;
}

type SourceStatus = "loading" | "available" | "unavailable" | "failed";

/** Automatically fetch one attributed forecast when a validated territory point is available. */
export function WeatherPanel({
  country,
  locale,
  point,
  refreshToken = 0,
}: Props) {
  const [sourceStatus, setSourceStatus] = useState<SourceStatus>("loading");
  const [sourceCountry, setSourceCountry] = useState("");
  const [sourceError, setSourceError] = useState("");
  const [sourceRetry, setSourceRetry] = useState(0);
  const [forecast, setForecast] = useState<WeatherForecast | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const tr = (key: TranslationKey, values?: Record<string, string | number>) =>
    t(locale, key, values);

  useEffect(() => {
    const controller = new AbortController();
    setSourceCountry(country);
    setSourceError("");
    setSourceStatus("loading");
    if (!country) return () => controller.abort();
    void listExternalSources(country, controller.signal).then((result) => {
      if (controller.signal.aborted) return;
      if (result.kind === "error") {
        setSourceError(result.code);
        setSourceStatus("failed");
        return;
      }
      setSourceStatus(
        result.data.some(
          (source) => source.country === country && source.id === "open-meteo",
        )
          ? "available"
          : "unavailable",
      );
    });
    return () => controller.abort();
  }, [country, sourceRetry]);

  const available = sourceCountry === country && sourceStatus === "available";
  const latitude = point?.latitude;
  const longitude = point?.longitude;
  useEffect(() => {
    const controller = new AbortController();
    setForecast(null);
    setError("");
    setBusy(false);
    if (!available || latitude === undefined || longitude === undefined)
      return () => controller.abort();
    setBusy(true);
    void readWeatherForecast({ latitude, longitude }, controller.signal).then(
      (result) => {
        if (controller.signal.aborted) return;
        setBusy(false);
        if (result.kind === "error") {
          setError(result.code);
          return;
        }
        if (
          result.data.requested_latitude !== latitude ||
          result.data.requested_longitude !== longitude
        ) {
          setError("INVALID_RESPONSE");
          return;
        }
        setForecast(result.data);
      },
    );
    return () => controller.abort();
  }, [available, latitude, longitude, refresh, refreshToken]);

  const number = (value: number | null) =>
    value === null
      ? tr("weatherMissing")
      : new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(
          value,
        );

  return (
    <section className="weather-panel" aria-label={tr("weatherTitle")}>
      <div className="section-header">
        <div className="label-with-help">
          <h2>{tr("weatherTitle")}</h2>
          <FieldHelp
            locale={locale}
            label="weatherTitle"
            explanation="weatherWarning"
          />
        </div>
        {point && available && (
          <button
            type="button"
            onClick={() => setRefresh((value) => value + 1)}
            disabled={busy}
          >
            {busy ? tr("weatherLoading") : tr("weatherRead")}
          </button>
        )}
      </div>
      {country && sourceCountry === country && sourceStatus === "loading" && (
        <p role="status" className="source-feedback source-feedback--loading">
          <span className="analysis-spinner" aria-hidden="true" />
          {tr("weatherCheckingSource")}
        </p>
      )}
      {country && sourceCountry === country && sourceStatus === "failed" && (
        <div className="source-feedback source-feedback--warning">
          <p role="alert">
            {tr("weatherSourceCheckFailed", { code: sourceError })}
          </p>
          <button
            type="button"
            className="source-retry"
            onClick={() => setSourceRetry((value) => value + 1)}
          >
            {tr("sourceRetry")}
          </button>
        </div>
      )}
      {country &&
        sourceCountry === country &&
        sourceStatus === "unavailable" && (
          <div className="source-feedback source-feedback--warning">
            <p role="status">{tr("weatherSourceUnavailable")}</p>
            <p className="field-help">{tr("weatherEnableHelp")}</p>
            <button
              type="button"
              className="source-retry"
              onClick={() => setSourceRetry((value) => value + 1)}
            >
              {tr("sourceRetry")}
            </button>
          </div>
        )}
      {!point && sourceStatus === "available" && (
        <p className="source-feedback">{tr("weatherSelectTerritory")}</p>
      )}
      {point && busy && (
        <p role="status" className="source-feedback source-feedback--loading">
          <span className="analysis-spinner" aria-hidden="true" />
          {tr("weatherLoading")}
        </p>
      )}
      {error && (
        <p role="alert" className="source-feedback source-feedback--warning">
          {tr("weatherError", { reason: error })}
        </p>
      )}
      {forecast && (
        <div role="status">
          <p className="field-help">
            {tr("weatherGrid", {
              lat: forecast.grid_latitude,
              lon: forecast.grid_longitude,
              time: forecast.captured_at,
            })}
          </p>
          <p className="warning-text">{tr("weatherWarning")}</p>
          {forecast.hours.length > 0 && (
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
                  {forecast.hours.slice(0, 1).map((hour) => (
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
          )}
          {forecast.hours.length > 1 && (
            <details className="weather-more">
              <summary>
                {tr("weatherMoreHours", { count: forecast.hours.length - 1 })}
              </summary>
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
                    {forecast.hours.slice(1).map((hour) => (
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
            </details>
          )}
          {forecast.uncertainties.map((note) => (
            <p className="warning-text" key={note}>
              {note}
            </p>
          ))}
          <a href={forecast.source_uri} rel="noopener noreferrer">
            {tr("weatherAttribution")}
          </a>
        </div>
      )}
    </section>
  );
}
