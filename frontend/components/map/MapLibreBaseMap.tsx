"use client";

import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import type { WorkspaceMapStatus, WorkspaceMapStyle } from "@/components/map/mapTypes";
import { resolveMapStyle } from "@/lib/map/styles";
import { useProjectStore } from "@/stores/projectStore";

interface MapLibreBaseMapProps {
  center: [number, number];
  zoom?: number;
  mapStyle: WorkspaceMapStyle;
  onMapReady: (map: maplibregl.Map) => void;
  onStatusChange?: (status: WorkspaceMapStatus) => void;
  onMapClick?: (lngLat: [number, number]) => void;
}

export default function MapLibreBaseMap({
  center,
  zoom = 15,
  mapStyle,
  onMapReady,
  onStatusChange,
  onMapClick,
}: MapLibreBaseMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const onMapReadyRef = useRef(onMapReady);
  const onStatusChangeRef = useRef(onStatusChange);
  const onMapClickRef = useRef(onMapClick);
  const setMapControls = useProjectStore((s) => s.setMapControls);
  const setMapReady = useProjectStore((s) => s.setMapReady);
  const setMapCursor = useProjectStore((s) => s.setMapCursor);

  useEffect(() => {
    onMapReadyRef.current = onMapReady;
    onStatusChangeRef.current = onStatusChange;
    onMapClickRef.current = onMapClick;
  }, [onMapReady, onMapClick, onStatusChange]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: resolveMapStyle(mapStyle),
      center,
      zoom,
      pitch: 58,
      bearing: -18,
      attributionControl: false,
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

    const emitStatus = () => {
      const c = map.getCenter();
      const status: WorkspaceMapStatus = {
        lngLat: [c.lng, c.lat],
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing(),
      };
      onStatusChangeRef.current?.(status);
      setMapCursor({
        lngLat: [c.lng, c.lat],
        zoom: status.zoom,
        bearing: status.bearing,
        scaleLabel: `z${status.zoom.toFixed(1)}`,
      });
    };

    map.on("load", () => {
      setMapReady(true);
      onMapReadyRef.current(map);
      setMapControls({
        flyHome: () => map.flyTo({ center, zoom, pitch: 58, bearing: -18, essential: true }),
        resetNorth: () => map.easeTo({ bearing: 0, pitch: map.getPitch(), essential: true }),
        zoomIn: () => map.zoomIn(),
        zoomOut: () => map.zoomOut(),
        fitToProject: () => map.flyTo({ center, zoom, essential: true }),
        getViewport: () => ({
          center: [map.getCenter().lng, map.getCenter().lat],
          zoom: map.getZoom(),
          bearing: map.getBearing(),
          pitch: map.getPitch(),
        }),
        flyToViewport: (viewport) => map.flyTo({ ...viewport, essential: true }),
      });
      emitStatus();
    });
    map.on("move", emitStatus);
    map.on("mousemove", (event) => {
      setMapCursor({
        lngLat: [event.lngLat.lng, event.lngLat.lat],
        zoom: map.getZoom(),
        bearing: map.getBearing(),
        scaleLabel: `z${map.getZoom().toFixed(1)}`,
      });
    });
    map.on("click", (event) => onMapClickRef.current?.([event.lngLat.lng, event.lngLat.lat]));

    return () => {
      setMapReady(false);
      setMapControls(null);
      setMapCursor(null);
      map.remove();
      mapRef.current = null;
    };
    // MapLibre must initialize once. Style changes are handled below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.setStyle(resolveMapStyle(mapStyle));
  }, [mapStyle]);

  return <div ref={containerRef} className="absolute inset-0" data-map-canvas="maplibre" />;
}
