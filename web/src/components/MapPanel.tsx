import { useEffect, useRef } from "react";
import L from "leaflet";
import type {
  Position,
  SaturnNotice,
  Stop,
  TerritoryGeometry,
} from "../api/types";
import { t } from "../i18n";
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
  referenceGeometry: TerritoryGeometry | null;
  saturnNotices: SaturnNotice[];
  onSelect: (siteId: string) => void;
  onPoint: (point: Position) => void;
}

/** Show OSM map tiles and restore the last browser-local camera position. */
export function MapPanel({
  locale,
  stops,
  selectedId,
  startingPoint,
  referenceGeometry,
  saturnNotices,
  onSelect,
  onPoint,
}: Props) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const overlays = useRef<L.LayerGroup | null>(null);
  const boundaryLayer = useRef<L.GeoJSON | null>(null);
  const treatmentLayer = useRef<L.LayerGroup | null>(null);
  const pointCallback = useRef(onPoint);
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

  useEffect(() => {
    if (!host.current) return;
    const instance = L.map(host.current, {
      zoomControl: true,
      attributionControl: true,
    });
    const saved = readMapViewport() ?? DEFAULT_VIEWPORT;
    instance.setView([saved.latitude, saved.longitude], saved.zoom);
    instance.on("moveend", () => {
      const center = instance.getCenter();
      saveMapViewport({
        latitude: center.lat,
        longitude: center.lng,
        zoom: instance.getZoom(),
      });
    });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: MAX_MAP_ZOOM,
      attribution: "© OpenStreetMap contributors",
    }).addTo(instance);
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
      treatmentLayer.current = null;
    };
  }, []);

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
      <div className="map-legend" aria-hidden="true">
        <span className="legend-dot" /> {t(locale, "mapProposed")}
        <span className="legend-dot legend-selected" />{" "}
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
