import { useEffect, useRef, useState } from "react";
import { searchSettlements } from "../api/client";
import type {
  CountryCode,
  SettlementSuggestion,
  Territory,
} from "../api/types";
import type { TerritoryNavigation } from "../hooks/useTerritoryReference";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";
import { FieldHelp } from "./FieldHelp";
import { ReferenceControls } from "./ReferenceControls";

interface Props {
  country: CountryCode;
  locale: Locale;
  regions: Territory[];
  navigation: TerritoryNavigation;
  catalogMessage: TranslationKey;
  onRetryRegions: () => void;
  coordinateStatus: "idle" | "checking" | "invalid" | "outside" | "unavailable";
  onCoordinatesEdited: () => void;
  onCoordinates: (latitude: string, longitude: string) => void;
}

/** Parse a pair without accepting ambiguous decimal-comma separators. */
export function splitCoordinateSearch(query: string): [string, string] | null {
  const fields = query.includes(";") ? query.split(";") : query.split(",");
  if (fields.length !== 2) return null;
  const latitude = fields[0]?.trim();
  const longitude = fields[1]?.trim();
  if (
    !latitude ||
    !longitude ||
    !/^[+-]?\d{1,3}(?:[.,]\d+)?$/.test(latitude) ||
    !/^[+-]?\d{1,3}(?:[.,]\d+)?$/.test(longitude)
  )
    return null;
  return [latitude, longitude];
}

/** Search names explicitly; the existing region-scoped point resolver validates selection. */
export function PlaceSearchToolbar({
  country,
  locale,
  regions,
  navigation,
  catalogMessage,
  onRetryRegions,
  coordinateStatus,
  onCoordinatesEdited,
  onCoordinates,
}: Props) {
  const tr = (key: TranslationKey) => t(locale, key);
  const [query, setQuery] = useState("");
  const [invalidQuery, setInvalidQuery] = useState(false);
  const [results, setResults] = useState<SettlementSuggestion[] | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const searchController = useRef<AbortController | null>(null);

  useEffect(() => {
    searchController.current?.abort();
    setQuery("");
    setInvalidQuery(false);
    setResults(null);
    setStatus("idle");
    return () => searchController.current?.abort();
  }, [country, navigation.regionId]);

  const search = () => {
    searchController.current?.abort();
    const pair = splitCoordinateSearch(query);
    if (pair) {
      setInvalidQuery(false);
      setResults(null);
      setStatus("idle");
      onCoordinates(pair[0], pair[1]);
      return;
    }
    const name = query.trim();
    if (name.length < 2 || name.length > 100) {
      setInvalidQuery(true);
      setResults(null);
      return;
    }
    setInvalidQuery(false);
    setStatus("loading");
    setResults(null);
    const controller = new AbortController();
    searchController.current = controller;
    void searchSettlements(country, name, locale, controller.signal).then(
      (response) => {
        if (controller.signal.aborted) return;
        setStatus(response.kind === "ok" ? "idle" : "error");
        setResults(
          response.kind === "ok"
            ? response.data.filter((place) => place.country === country)
            : null,
        );
      },
    );
  };

  return (
    <div
      className="place-search-toolbar"
      role="region"
      aria-label={tr("workspaceFindPlace")}
    >
      <ReferenceControls
        locale={locale}
        regions={regions}
        navigation={navigation}
        catalogMessage={catalogMessage}
        onRetryRegions={onRetryRegions}
      />
      <form
        className="place-coordinate-search"
        onSubmit={(event) => {
          event.preventDefault();
          search();
        }}
      >
        <div className="label-with-help">
          <label htmlFor="place-coordinate-query">
            {tr("workspaceCoordinateSearch")}
          </label>
          <FieldHelp
            locale={locale}
            label="workspaceCoordinateSearch"
            explanation="workspaceSearchNote"
          />
        </div>
        <div className="place-coordinate-search-row">
          <input
            id="place-coordinate-query"
            value={query}
            disabled={!navigation.regionId}
            placeholder={tr("workspaceCoordinateExample")}
            autoComplete="off"
            onChange={(event) => {
              searchController.current?.abort();
              setQuery(event.target.value);
              setResults(null);
              setStatus("idle");
              setInvalidQuery(false);
              onCoordinatesEdited();
            }}
          />
          <button
            type="submit"
            disabled={
              !navigation.regionId ||
              status === "loading" ||
              coordinateStatus === "checking"
            }
          >
            {status === "loading" || coordinateStatus === "checking"
              ? tr("workspaceSearching")
              : tr("workspaceFindOnMap")}
          </button>
        </div>
        {!navigation.regionId && (
          <p className="field-help" role="status">
            {tr("workspaceSearchNeedsRegion")}
          </p>
        )}
        {status === "loading" && (
          <p role="status" className="field-help">
            {tr("workspaceSearching")}
          </p>
        )}
        {status === "error" && (
          <p role="alert" className="field-help">
            {tr("workspaceSearchUnavailable")}
          </p>
        )}
        {invalidQuery && (
          <p role="status" className="field-help">
            {tr("workspaceSearchInvalid")}
          </p>
        )}
        {results && (
          <div
            className="place-search-results"
            aria-label={tr("workspaceSearchResults")}
          >
            {results.length === 0 ? (
              <p role="status">{tr("workspaceSearchEmpty")}</p>
            ) : (
              <ul>
                {results.map((place) => (
                  <li key={place.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setResults(null);
                        onCoordinates(
                          String(place.latitude),
                          String(place.longitude),
                        );
                      }}
                    >
                      <strong>{place.name}</strong>
                      {place.admin1 && <span>{place.admin1}</span>}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <a
              href="https://open-meteo.com/en/docs/geocoding-api"
              target="_blank"
              rel="noopener noreferrer"
            >
              {tr("workspaceSearchAttribution")}
            </a>
          </div>
        )}
        {coordinateStatus === "invalid" && (
          <p role="status" className="field-help">
            {tr("draftAreaCoordinateInvalid")}
          </p>
        )}
        {(coordinateStatus === "outside" ||
          coordinateStatus === "unavailable") && (
          <p role="status" className="field-help">
            {tr(
              coordinateStatus === "outside"
                ? "draftAreaCoordinateOutside"
                : "draftAreaCoordinateUnavailable",
            )}
          </p>
        )}
      </form>
    </div>
  );
}
