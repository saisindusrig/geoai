"use client";

import { MapboxOverlay } from "@deck.gl/mapbox";
import type { Layer } from "@deck.gl/core";
import type maplibregl from "maplibre-gl";
import { useEffect, useMemo, useRef } from "react";
import type { WorkspaceFeatureCollection } from "@/components/map/mapTypes";
import { google3DTilesLayer } from "@/components/map/Google3DTilesLayer";
import { aiPlaceholderLayer, drawnGeoJsonLayer } from "@/lib/map/layers";
import { designModelLayer } from "@/lib/map/design-model-layer";

interface DeckOverlayProps {
  map: maplibregl.Map | null;
  features: WorkspaceFeatureCollection;
  selectedId?: string | null;
  google3dEnabled: boolean;
  aiPlaceholderEnabled?: boolean;
  modelUrl?: string | null;
  modelCenter?: [number, number];
  modelAlignment?: import("@/lib/types").GeoJSONGeometry | null;
}

export default function DeckOverlay({
  map,
  features,
  selectedId,
  google3dEnabled,
  aiPlaceholderEnabled = true,
  modelUrl,
  modelCenter,
  modelAlignment,
}: DeckOverlayProps) {
  const overlayRef = useRef<MapboxOverlay | null>(null);

  const layers = useMemo(() => {
    const next: Layer[] = [drawnGeoJsonLayer(features, selectedId)];
    if (aiPlaceholderEnabled) next.push(aiPlaceholderLayer(features));
    if (modelUrl && modelCenter) {
      next.push(
        designModelLayer({
          modelUrl,
          centerLng: modelCenter[0],
          centerLat: modelCenter[1],
          alignment: modelAlignment ?? null,
          opacity: 0.92,
        }),
      );
    }
    const google = google3DTilesLayer(google3dEnabled);
    if (google) next.push(google as unknown as Layer);
    return next;
  }, [aiPlaceholderEnabled, features, google3dEnabled, modelAlignment, modelCenter, modelUrl, selectedId]);

  useEffect(() => {
    if (!map) return;
    if (!overlayRef.current) {
      overlayRef.current = new MapboxOverlay({ interleaved: false, layers });
      map.addControl(overlayRef.current as unknown as maplibregl.IControl);
    }
    overlayRef.current.setProps({ layers });
  }, [layers, map]);

  useEffect(
    () => () => {
      if (overlayRef.current && map) {
        try {
          map.removeControl(overlayRef.current as unknown as maplibregl.IControl);
        } catch {
          // MapLibre may already be disposed during route teardown.
        }
      }
      overlayRef.current = null;
    },
    [map],
  );

  return null;
}
