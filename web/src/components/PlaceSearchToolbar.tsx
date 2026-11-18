import { useEffect, useState } from "react";
import type { Territory } from "../api/types";
import type { TerritoryNavigation } from "../hooks/useTerritoryReference";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";
import { ReferenceControls } from "./ReferenceControls";

interface Props {
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
  if (!latitude || !longitude) return null;
  return [latitude, longitude];
}

/** A region-scoped coordinate search; a settlement catalog is not yet available. */
export function PlaceSearchToolbar({
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
  useEffect(() => {
    setQuery("");
    setInvalidQuery(false);
  }, [navigation.regionId]);

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
          const pair = splitCoordinateSearch(query);
          if (!pair) {
            setInvalidQuery(true);
            return;
          }
          setInvalidQuery(false);
          onCoordinates(pair[0], pair[1]);
        }}
      >
        <label htmlFor="place-coordinate-query">
          {tr("workspaceCoordinateSearch")}
        </label>
        <div className="place-coordinate-search-row">
          <input
            id="place-coordinate-query"
            value={query}
            disabled={!navigation.regionId}
            placeholder={tr("workspaceCoordinateExample")}
            autoComplete="off"
            onChange={(event) => {
              setQuery(event.target.value);
              setInvalidQuery(false);
              onCoordinatesEdited();
            }}
          />
          <button
            type="submit"
            disabled={!navigation.regionId || coordinateStatus === "checking"}
          >
            {coordinateStatus === "checking"
              ? tr("draftAreaVerifying")
              : tr("workspaceFindOnMap")}
          </button>
        </div>
        <p className="field-help">
          {tr(
            navigation.regionId
              ? "workspaceSearchNote"
              : "workspaceSearchNeedsRegion",
          )}
        </p>
        {(invalidQuery || coordinateStatus === "invalid") && (
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
