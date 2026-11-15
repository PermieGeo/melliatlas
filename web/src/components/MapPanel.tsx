import { useEffect, useRef } from "react";
import L from "leaflet";
import type { Position, Stop } from "../api/types";
import { t } from "../i18n";
import type { Locale } from "../i18n";

/** Render-only Leaflet inputs; user coordinates are never logged or persisted. */
interface Props {
  locale: Locale;
  stops: Stop[];
  selectedId: string | null;
  startingPoint: Position | null;
  showTiles: boolean;
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
  onSelect,
  onPoint,
}: Props) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const overlays = useRef<L.LayerGroup | null>(null);
  const tiles = useRef<L.TileLayer | null>(null);
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
      </div>
      <p className="map-note">{t(locale, "mapNote")}</p>
    </div>
  );
}
