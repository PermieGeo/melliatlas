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

/** Render-only Leaflet inputs; user coordinates are never logged or persisted. */
interface Props {
  locale: Locale;
  stops: Stop[];
  selectedId: string | null;
  startingPoint: Position | null;
  showTiles: boolean;
  referenceGeometry: TerritoryGeometry | null;
  saturnNotices: SaturnNotice[];
  onSelect: (siteId: string) => void;
  onPoint: (point: Position) => void;
}

/** The basemap is opt-in because remote tile services observe approximate viewports. */
export function MapPanel({
  locale,
  stops,
  selectedId,
  startingPoint,
  showTiles,
  referenceGeometry,
  saturnNotices,
  onSelect,
  onPoint,
}: Props) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const overlays = useRef<L.LayerGroup | null>(null);
  const tiles = useRef<L.TileLayer | null>(null);
  const boundaryLayer = useRef<L.GeoJSON | null>(null);
  const treatmentLayer = useRef<L.LayerGroup | null>(null);
  const pointCallback = useRef(onPoint);
  pointCallback.current = onPoint;

  useEffect(() => {
    if (!host.current) return;
    const instance = L.map(host.current, {
      zoomControl: true,
      attributionControl: true,
    });
    instance.setView([0, 0], 2);
    instance.on("click", (event: L.LeafletMouseEvent) => {
      pointCallback.current({
        longitude: Number(event.latlng.lng.toFixed(5)),
        latitude: Number(event.latlng.lat.toFixed(5)),
      });
    });
    const layer = L.layerGroup().addTo(instance);
    map.current = instance;
    overlays.current = layer;
    return () => {
      instance.remove();
      map.current = null;
      overlays.current = null;
      tiles.current = null;
      boundaryLayer.current = null;
      treatmentLayer.current = null;
    };
  }, []);

  useEffect(() => {
    const instance = map.current;
    if (!instance) return;
    if (showTiles && tiles.current === null) {
      tiles.current = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          maxZoom: 18,
          attribution: "© OpenStreetMap contributors",
        },
      ).addTo(instance);
    }
    if (!showTiles && tiles.current !== null) {
      instance.removeLayer(tiles.current);
      tiles.current = null;
    }
  }, [showTiles]);

  useEffect(() => {
    const layer = overlays.current;
    const instance = map.current;
    if (!layer || !instance) return;
    layer.clearLayers();
    for (const stop of stops) {
      const active = selectedId === stop.site_id;
      const marker = L.circleMarker([stop.latitude, stop.longitude], {
        radius: active ? 11 : 8,
        weight: active ? 3 : 2,
        color: active ? "#263a28" : "#456b5a",
        fillColor: active ? "#f4b75c" : "#a8d5b6",
        fillOpacity: 0.95,
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
          radius: 6,
          color: "#355d9a",
          fillColor: "#fff",
          fillOpacity: 1,
          weight: 3,
        },
      );
      point.bindTooltip(t(locale, "mapStartingPoint"));
      layer.addLayer(point);
    }
    if (stops.length === 0 && startingPoint !== null) {
      instance.setView([startingPoint.latitude, startingPoint.longitude], 9);
    }
    if (stops.length > 0) {
      const bounds = L.latLngBounds(
        stops.map((stop) => L.latLng(stop.latitude, stop.longitude)),
      );
      instance.fitBounds(bounds.pad(0.3), { maxZoom: 11, animate: false });
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
      style: {
        color: "#6475a2",
        weight: 2,
        fillColor: "#9aa7cf",
        fillOpacity: 0.14,
      },
      interactive: false,
    }).addTo(instance);
    boundaryLayer.current = boundary;
    if (!stops.length && startingPoint === null) {
      instance.fitBounds(boundary.getBounds(), { animate: false });
    }
  }, [referenceGeometry, stops.length, startingPoint]);

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
        style: {
          color: "#c57832",
          fillColor: "#edaf75",
          fillOpacity: 0.24,
          weight: 2,
        },
      });
      polygon.bindTooltip(`${notice.source_id} / ${notice.record_id}`);
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
          <> · {t(locale, "saturnTitle")}</>
        )}
      </div>
      <p className="map-note">{t(locale, "mapNote")}</p>
    </div>
  );
}
