"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoPoint } from "@/lib/civicspan";
import type {
  ConstructionSpec,
  ConstructionStage,
} from "@/lib/construction";
import ConstructionMapOverlay, {
  type ConstructionMapPlacement,
} from "./ConstructionMapOverlay";

export type SiteMapEndpoint = "start" | "end";

type Props = {
  start: GeoPoint;
  end: GeoPoint;
  onPointsChange: (start: GeoPoint, end: GeoPoint) => void;
  activeEndpoint?: SiteMapEndpoint;
  onActiveEndpointChange?: (endpoint: SiteMapEndpoint) => void;
  fitRequest?: number;
  constructionSpec?: ConstructionSpec;
  constructionStage?: ConstructionStage;
  constructionPlacement?: ConstructionMapPlacement;
  showConstruction?: boolean;
  constructionModelUrl?: string;
};

const mapStyle = {
  version: 8 as const,
  sources: {
    osm: {
      type: "raster" as const,
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
};

function selectedFeatures(start: GeoPoint, end: GeoPoint) {
  return {
    type: "FeatureCollection" as const,
    features: [
      {
        type: "Feature" as const,
        properties: { kind: "anchor", label: "START", color: "#b2bbab" },
        geometry: {
          type: "Point" as const,
          coordinates: [start.lng, start.lat],
        },
      },
      {
        type: "Feature" as const,
        properties: { kind: "anchor", label: "END", color: "#8ea0a3" },
        geometry: { type: "Point" as const, coordinates: [end.lng, end.lat] },
      },
      {
        type: "Feature" as const,
        properties: { kind: "corridor" },
        geometry: {
          type: "LineString" as const,
          coordinates: [
            [start.lng, start.lat],
            [end.lng, end.lat],
          ],
        },
      },
    ],
  };
}

function fitToSelection(map: MapLibreMap, start: GeoPoint, end: GeoPoint) {
  const bounds = new maplibregl.LngLatBounds(
    [start.lng, start.lat],
    [start.lng, start.lat],
  );
  bounds.extend([end.lng, end.lat]);
  map.fitBounds(bounds, {
    padding: { top: 80, right: 48, bottom: 80, left: 48 },
    maxZoom: 16.5,
    duration: 450,
  });
}

export default function SiteMap({
  start,
  end,
  onPointsChange,
  activeEndpoint,
  onActiveEndpointChange,
  fitRequest = 0,
  constructionSpec,
  constructionStage = "finish",
  constructionPlacement,
  showConstruction = true,
  constructionModelUrl,
}: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const points = useRef({ start, end });
  const onPointsChangeRef = useRef(onPointsChange);
  const [internalEndpoint, setInternalEndpoint] =
    useState<SiteMapEndpoint>("start");
  const endpoint = activeEndpoint ?? internalEndpoint;
  const endpointRef = useRef<SiteMapEndpoint>(endpoint);
  const [ready, setReady] = useState(false);
  const [mapInstance, setMapInstance] = useState<MapLibreMap | null>(null);
  const [mapNotice, setMapNotice] = useState<string | null>(null);

  useEffect(() => {
    points.current = { start, end };
    const instance = map.current;
    const source = instance?.getSource("geoai-selection") as
      maplibregl.GeoJSONSource | undefined;
    source?.setData(selectedFeatures(start, end));
    if (instance && ready) fitToSelection(instance, start, end);
  }, [start, end, ready]);

  useEffect(() => {
    onPointsChangeRef.current = onPointsChange;
  }, [onPointsChange]);

  useEffect(() => {
    endpointRef.current = endpoint;
  }, [endpoint]);

  const selectEndpoint = useCallback(
    (nextEndpoint: SiteMapEndpoint) => {
      setInternalEndpoint(nextEndpoint);
      onActiveEndpointChange?.(nextEndpoint);
    },
    [onActiveEndpointChange],
  );

  useEffect(() => {
    if (fitRequest > 0 && map.current) {
      fitToSelection(map.current, points.current.start, points.current.end);
    }
  }, [fitRequest]);

  useEffect(() => {
    if (!container.current || map.current) return;
    const initial = points.current;
    let reportedImageryProblem = false;
    const instance = new maplibregl.Map({
      container: container.current,
      style: mapStyle,
      center: [
        (initial.start.lng + initial.end.lng) / 2,
        (initial.start.lat + initial.end.lat) / 2,
      ],
      zoom: 15.2,
      pitch: 42,
      bearing: -18,
      attributionControl: false,
    });
    map.current = instance;
    setMapInstance(instance);
    instance.addControl(
      new maplibregl.NavigationControl({ visualizePitch: true }),
      "top-right",
    );
    instance.addControl(
      new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }),
      "bottom-left",
    );
    instance.addControl(
      new maplibregl.AttributionControl({ compact: true }),
      "bottom-right",
    );
    instance.on("load", () => {
      instance.addSource("geoai-selection", {
        type: "geojson",
        data: selectedFeatures(points.current.start, points.current.end),
      });
      instance.addLayer({
        id: "geoai-corridor-outline",
        type: "line",
        source: "geoai-selection",
        filter: ["==", ["get", "kind"], "corridor"],
        paint: {
          "line-color": "#060706",
          "line-width": 9,
          "line-opacity": 0.9,
        },
      });
      instance.addLayer({
        id: "geoai-corridor",
        type: "line",
        source: "geoai-selection",
        filter: ["==", ["get", "kind"], "corridor"],
        paint: {
          "line-color": "#b2bbab",
          "line-width": 4,
          "line-opacity": 0.98,
          "line-dasharray": [1.2, 1.1],
        },
      });
      instance.addLayer({
        id: "geoai-anchors",
        type: "circle",
        source: "geoai-selection",
        filter: ["==", ["get", "kind"], "anchor"],
        paint: {
          "circle-radius": 9,
          "circle-color": ["get", "color"],
          "circle-stroke-color": "#f8fafc",
          "circle-stroke-width": 3,
        },
      });
      instance.addLayer({
        id: "geoai-anchor-labels",
        type: "symbol",
        source: "geoai-selection",
        filter: ["==", ["get", "kind"], "anchor"],
        layout: {
          "text-field": ["get", "label"],
          "text-size": 11,
          "text-offset": [0, -1.8],
          "text-anchor": "bottom",
          "text-letter-spacing": 0.08,
        },
        paint: {
          "text-color": "#f8fafc",
          "text-halo-color": "#0f172a",
          "text-halo-width": 1.5,
        },
      });
      setReady(true);
    });
    instance.on("click", (event) => {
      const point = {
        lng: Number(event.lngLat.lng.toFixed(6)),
        lat: Number(event.lngLat.lat.toFixed(6)),
      };
      const next =
        endpointRef.current === "start"
          ? { start: point, end: points.current.end }
          : { start: points.current.start, end: point };
      onPointsChangeRef.current(next.start, next.end);
      selectEndpoint(endpointRef.current === "start" ? "end" : "start");
    });
    instance.on("error", (event) => {
      const sourceId = (event as { sourceId?: string }).sourceId;
      if (!reportedImageryProblem && sourceId === "osm") {
        reportedImageryProblem = true;
        setMapNotice(
          "Some map imagery could not load. You can still place endpoints and use the bridge overlay.",
        );
      }
    });
    return () => {
      setMapInstance(null);
      instance.remove();
      map.current = null;
    };
  }, [selectEndpoint]);

  const useMyLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setMapNotice(
        "This browser does not provide location access. Choose the endpoint directly on the map.",
      );
      return;
    }
    setMapNotice(null);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const point = {
          lng: Number(coords.longitude.toFixed(6)),
          lat: Number(coords.latitude.toFixed(6)),
        };
        const next =
          endpointRef.current === "start"
            ? { start: point, end: points.current.end }
            : { start: points.current.start, end: point };
        onPointsChangeRef.current(next.start, next.end);
        selectEndpoint(endpointRef.current === "start" ? "end" : "start");
      },
      () =>
        setMapNotice(
          "Location access was not granted. Choose the endpoint directly on the map.",
        ),
      { enableHighAccuracy: true, maximumAge: 60_000, timeout: 10_000 },
    );
  }, [selectEndpoint]);

  return (
    <div
      className="relative h-full min-h-[420px] w-full"
      aria-label="Interactive bridge site map"
    >
      <div
        ref={container}
        className="absolute inset-0"
        data-map-canvas="maplibre"
      />
      {constructionSpec && constructionPlacement && (
        <ConstructionMapOverlay
          map={mapInstance}
          spec={constructionSpec}
          stage={constructionStage}
          start={start}
          end={end}
          placement={constructionPlacement}
          visible={showConstruction}
          modelUrl={constructionModelUrl}
        />
      )}
      <div className="pointer-events-none absolute left-3 top-3 z-10 max-w-[calc(100%-5rem)] rounded-xl border border-border bg-background/90 p-1.5 shadow-xl backdrop-blur">
        <div
          className="pointer-events-auto flex items-center gap-1"
          role="group"
          aria-label="Endpoint being placed"
        >
          {(["start", "end"] as SiteMapEndpoint[]).map((item) => (
            <button
              type="button"
              key={item}
              onClick={() => selectEndpoint(item)}
              className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition ${endpoint === item ? "bg-primary text-primary-foreground" : "text-foreground-secondary hover:bg-surface-hover"}`}
              aria-pressed={endpoint === item}
            >
              Set {item}
            </button>
          ))}
        </div>
        <p className="px-1.5 pt-1 text-[10px] text-muted-foreground">
          Click the map to place the {endpoint} endpoint.
        </p>
      </div>
      <div className="absolute bottom-8 right-3 z-10 flex gap-2">
        <button
          type="button"
          onClick={useMyLocation}
          className="rounded-lg border border-border bg-background/90 px-2.5 py-1.5 text-xs font-medium text-foreground shadow-xl backdrop-blur hover:bg-surface-hover"
        >
          Use my location
        </button>
        <button
          type="button"
          onClick={() =>
            map.current &&
            fitToSelection(
              map.current,
              points.current.start,
              points.current.end,
            )
          }
          className="rounded-lg border border-border bg-background/90 px-2.5 py-1.5 text-xs font-medium text-foreground shadow-xl backdrop-blur hover:bg-surface-hover"
        >
          Fit bridge
        </button>
      </div>
      {!ready && !mapNotice && (
        <div className="pointer-events-none absolute inset-0 grid place-items-center bg-background/60 text-xs text-muted-foreground">
          Loading map…
        </div>
      )}
      {mapNotice && (
        <p className="absolute bottom-3 left-3 right-3 z-10 rounded-lg border border-warning/20 bg-background/90 p-2 text-[11px] leading-4 text-warning-text shadow-xl">
          {mapNotice}
        </p>
      )}
    </div>
  );
}
