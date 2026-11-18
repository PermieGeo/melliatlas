import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type {
  Position,
  SaturnNotice,
  Stop,
  TerritoryGeometry,
} from "../api/types";
import { t } from "../i18n";
import { dimensionFromDraftEdge } from "../geo/analysisDraft";
import type { DraftRectangle } from "../geo/analysisDraft";
import type { Locale } from "../i18n";
import {
  DEFAULT_VIEWPORT,
  MAX_MAP_ZOOM,
  readMapViewport,
  saveMapViewport,
} from "../geo/viewport";

// Display-only camera limits and marker sizes; none represents a safe distance.
const SATURN_FOCUS_MAX_ZOOM = 13;
const TERRITORY_FIT_MAX_ZOOM = 11;
const SITE_FIT_MAX_ZOOM = 11;
const SITE_BOUNDS_PADDING_FACTOR = 0.3;
const TERRITORY_FIT_PADDING_PX = 12;
const SELECTED_SITE_MARKER_RADIUS_PX = 11;
const SITE_MARKER_RADIUS_PX = 8;
const STARTING_POINT_MARKER_RADIUS_PX = 6;
// Click selection precision is not cadastral or geodesic precision.
const MAP_CLICK_COORDINATE_DECIMALS = 5;

/** The selected apiary point stays in memory; only the general map camera is stored. */
interface Props {
  locale: Locale;
  stops: Stop[];
  selectedId: string | null;
  startingPoint: Position | null;
  draftPoint: Position | null;
  draftBounds: DraftRectangle | null;
  privateFocus: Position | null;
  referenceGeometry: TerritoryGeometry | null;
  previewDistrictGeometry: TerritoryGeometry | null;
  saturnNotices: SaturnNotice[];
  onSelect: (siteId: string) => void;
  onPoint: (point: Position) => void;
  onDraftResize: (axis: "widthKm" | "heightKm", value: number) => void;
}

/** Restore the browser-local camera without contacting a remote tile provider by default. */
export function MapPanel({
  locale,
  stops,
  selectedId,
  startingPoint,
  draftPoint,
  draftBounds,
  privateFocus,
  referenceGeometry,
  previewDistrictGeometry,
  saturnNotices,
  onSelect,
  onPoint,
  onDraftResize,
}: Props) {
  const [onlineBasemap, setOnlineBasemap] = useState(false);
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const overlays = useRef<L.LayerGroup | null>(null);
  const boundaryLayer = useRef<L.GeoJSON | null>(null);
  const previewDistrictLayer = useRef<L.GeoJSON | null>(null);
  const treatmentLayer = useRef<L.LayerGroup | null>(null);
  const draftLayer = useRef<L.LayerGroup | null>(null);
  const pointCallback = useRef(onPoint);
  const resizeCallback = useRef(onDraftResize);
  const privateCamera = useRef(false);
  const focusTreatment = () => {
    const instance = map.current;
    const layer = treatmentLayer.current;
    if (!instance || !layer || layer.getLayers().length === 0) return;
    const bounds = L.featureGroup(layer.getLayers()).getBounds();
    if (bounds.isValid())
      instance.fitBounds(bounds, {
        animate: false,
        maxZoom: SATURN_FOCUS_MAX_ZOOM,
      });
  };
  pointCallback.current = onPoint;
  resizeCallback.current = onDraftResize;

  useEffect(() => {
    if (!host.current) return;
    const instance = L.map(host.current, {
      zoomControl: true,
      attributionControl: true,
    });
    const saved = readMapViewport() ?? DEFAULT_VIEWPORT;
    instance.setView([saved.latitude, saved.longitude], saved.zoom);
    instance.on("moveend", () => {
      if (privateCamera.current) return;
      const center = instance.getCenter();
      saveMapViewport({
        latitude: center.lat,
        longitude: center.lng,
        zoom: instance.getZoom(),
      });
    });
    instance.on("click", (event: L.LeafletMouseEvent) => {
      pointCallback.current({
        longitude: Number(
          event.latlng.lng.toFixed(MAP_CLICK_COORDINATE_DECIMALS),
        ),
        latitude: Number(
          event.latlng.lat.toFixed(MAP_CLICK_COORDINATE_DECIMALS),
        ),
      });
    });
    const layer = L.layerGroup().addTo(instance);
    map.current = instance;
    overlays.current = layer;
    return () => {
      instance.remove();
      map.current = null;
      overlays.current = null;
      boundaryLayer.current = null;
      previewDistrictLayer.current = null;
      treatmentLayer.current = null;
      draftLayer.current = null;
    };
  }, []);

  useEffect(() => {
    if (!privateFocus) return;
    const instance = map.current;
    if (!instance) return;
    // A privately entered coordinate must not become a persisted map camera.
    privateCamera.current = true;
    instance.setView(
      [privateFocus.latitude, privateFocus.longitude],
      instance.getZoom(),
      { animate: false },
    );
  }, [privateFocus]);

  useEffect(() => {
    const instance = map.current;
    if (!instance || !onlineBasemap) return;
    const tiles = L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: MAX_MAP_ZOOM,
        attribution: "© OpenStreetMap contributors",
      },
    ).addTo(instance);
    return () => {
      instance.removeLayer(tiles);
    };
  }, [onlineBasemap]);

  useEffect(() => {
    const layer = overlays.current;
    const instance = map.current;
    if (!layer || !instance) return;
    layer.clearLayers();
    for (const stop of stops) {
      const active = selectedId === stop.site_id;
      const marker = L.circleMarker([stop.latitude, stop.longitude], {
        radius: active ? SELECTED_SITE_MARKER_RADIUS_PX : SITE_MARKER_RADIUS_PX,
        className: active
          ? "ma-site-marker ma-site-selected"
          : "ma-site-marker",
      });
      marker.bindTooltip(stop.site_id, { direction: "top" });
      marker.on("click", (event: L.LeafletMouseEvent) => {
        L.DomEvent.stopPropagation(event);
        onSelect(stop.site_id);
      });
      layer.addLayer(marker);
    }
    if (startingPoint !== null) {
      const point = L.circleMarker(
        [startingPoint.latitude, startingPoint.longitude],
        {
          radius: STARTING_POINT_MARKER_RADIUS_PX,
          className: "ma-starting-point",
        },
      );
      point.bindTooltip(t(locale, "mapStartingPoint"));
      layer.addLayer(point);
    }
    if (stops.length > 0) {
      const bounds = L.latLngBounds(
        stops.map((stop) => L.latLng(stop.latitude, stop.longitude)),
      );
      instance.fitBounds(bounds.pad(SITE_BOUNDS_PADDING_FACTOR), {
        maxZoom: SITE_FIT_MAX_ZOOM,
        animate: false,
      });
    }
  }, [locale, onSelect, selectedId, startingPoint, stops]);

  useEffect(() => {
    const instance = map.current;
    if (!instance) return;
    if (draftLayer.current) instance.removeLayer(draftLayer.current);
    const layer = L.layerGroup().addTo(instance);
    draftLayer.current = layer;
    if (draftBounds) {
      for (const [west, east] of draftBounds.longitudeRanges) {
        layer.addLayer(
          L.rectangle(
            [
              [draftBounds.south, west],
              [draftBounds.north, east],
            ],
            { className: "ma-analysis-draft", interactive: false },
          ),
        );
      }
    }
    if (draftPoint) {
      layer.addLayer(
        L.circleMarker([draftPoint.latitude, draftPoint.longitude], {
          radius: STARTING_POINT_MARKER_RADIUS_PX,
          className: "ma-analysis-draft-point",
          interactive: false,
        }),
      );
    }
    if (draftPoint && draftBounds) {
      const east = draftBounds.longitudeRanges.at(-1)?.[1];
      const addResizeHandle = (
        axis: "widthKm" | "heightKm",
        position: Position,
      ) => {
        const anchor = L.latLng(position.latitude, position.longitude);
        const marker = L.marker(anchor, {
          draggable: true,
          bubblingMouseEvents: false,
          keyboard: true,
          title: t(
            locale,
            axis === "widthKm" ? "draftAreaWidth" : "draftAreaHeight",
          ),
          icon: L.divIcon({
            className: `ma-draft-resize-handle ma-draft-resize-${axis}`,
            iconSize: [18, 18],
            iconAnchor: [9, 9],
          }),
        });
        marker.bindTooltip(
          t(locale, axis === "widthKm" ? "draftAreaWidth" : "draftAreaHeight"),
        );
        marker.on("click", (event: L.LeafletMouseEvent) =>
          L.DomEvent.stopPropagation(event),
        );
        marker.on("dragend", () => {
          const moved = marker.getLatLng();
          marker.setLatLng(anchor);
          const dimension = dimensionFromDraftEdge(draftPoint, axis, {
            latitude: moved.lat,
            longitude: moved.lng,
          });
          if (dimension !== null) resizeCallback.current(axis, dimension);
        });
        layer.addLayer(marker);
      };
      if (east !== undefined) {
        addResizeHandle("widthKm", {
          latitude: draftPoint.latitude,
          longitude: east,
        });
      }
      addResizeHandle("heightKm", {
        latitude: draftBounds.north,
        longitude: draftPoint.longitude,
      });
    }
    return () => {
      instance.removeLayer(layer);
      if (draftLayer.current === layer) draftLayer.current = null;
    };
  }, [draftBounds, draftPoint, locale]);

  useEffect(() => {
    const instance = map.current;
    if (!instance) return;
    if (boundaryLayer.current) {
      instance.removeLayer(boundaryLayer.current);
      boundaryLayer.current = null;
    }
    if (!referenceGeometry) return;
    // Only the validated server reference is used to draw administrative geometry.
    const boundary = L.geoJSON(referenceGeometry.geometry, {
      style: { className: "ma-reference-boundary" },
      interactive: false,
    }).addTo(instance);
    boundaryLayer.current = boundary;
    // An explicit territory choice takes precedence over previous stops and viewport.
    const bounds = boundary.getBounds();
    if (bounds.isValid()) {
      instance.fitBounds(bounds, {
        animate: false,
        maxZoom: TERRITORY_FIT_MAX_ZOOM,
        padding: [TERRITORY_FIT_PADDING_PX, TERRITORY_FIT_PADDING_PX],
      });
    }
  }, [referenceGeometry]);

  useEffect(() => {
    const instance = map.current;
    if (!instance) return;
    if (previewDistrictLayer.current) {
      instance.removeLayer(previewDistrictLayer.current);
      previewDistrictLayer.current = null;
    }
    if (!previewDistrictGeometry) return;
    // Public reference outlines never change the draft's current map camera.
    const boundary = L.geoJSON(previewDistrictGeometry.geometry, {
      style: { className: "ma-area-preview-district" },
      interactive: false,
    }).addTo(instance);
    previewDistrictLayer.current = boundary;
    return () => {
      instance.removeLayer(boundary);
      if (previewDistrictLayer.current === boundary) {
        previewDistrictLayer.current = null;
      }
    };
  }, [previewDistrictGeometry]);

  useEffect(() => {
    const instance = map.current;
    if (!instance) return;
    if (treatmentLayer.current) instance.removeLayer(treatmentLayer.current);
    const group = L.layerGroup().addTo(instance);
    treatmentLayer.current = group;
    const geometries = saturnNotices.filter(
      (notice) => notice.geometry !== null,
    );
    for (const notice of geometries) {
      if (!notice.geometry) continue;
      const polygon = L.geoJSON(notice.geometry, {
        style: { className: "ma-saturn-polygon" },
      });
      polygon.bindTooltip(`${notice.source_id} / ${notice.record_id}`);
      polygon.on("click", (event: L.LeafletMouseEvent) =>
        L.DomEvent.stopPropagation(event),
      );
      group.addLayer(polygon);
    }
    if (
      startingPoint === null &&
      !referenceGeometry &&
      group.getLayers().length
    ) {
      const bounds = L.featureGroup(group.getLayers()).getBounds();
      if (bounds.isValid()) instance.fitBounds(bounds, { animate: false });
    }
    return () => {
      instance.removeLayer(group);
      if (treatmentLayer.current === group) treatmentLayer.current = null;
    };
  }, [saturnNotices, referenceGeometry, startingPoint, stops.length]);

  return (
    <div className="map-shell">
      <div
        ref={host}
        className="map-canvas"
        role="application"
        aria-label={t(locale, "mapLabel")}
      />
      <div className="map-legend">
        <label className="map-basemap-control">
          <input
            type="checkbox"
            checked={onlineBasemap}
            onChange={(event) => setOnlineBasemap(event.target.checked)}
          />
          {t(locale, "mapOnlineBasemap")}
        </label>
        <span className="legend-dot" aria-hidden="true" />{" "}
        {t(locale, "mapProposed")}
        <span className="legend-dot legend-selected" aria-hidden="true" />{" "}
        {t(locale, "mapSelected")}
        {saturnNotices.some((notice) => notice.geometry !== null) && (
          <>
            {" · "}
            {t(locale, "saturnTitle")}
            <button type="button" onClick={focusTreatment}>
              {t(locale, "mapShowSaturnFields")}
            </button>
          </>
        )}
      </div>
      <p className="map-note">{t(locale, "mapNote")}</p>
    </div>
  );
}
