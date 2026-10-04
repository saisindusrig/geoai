"use client";

import maplibregl, { Map as MlMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  formatAreaForUnit,
  formatDistanceForUnit,
  bboxFromGeometries,
  haversineM,
  lineLengthM,
  mapScaleLabel,
  polygonAreaSqm,
} from "@/lib/geo";
import {
  corridorFromLine,
  geometryToVertices,
  rectangleFromCorners,
  snapPointToFeatures,
  toolInstruction,
  verticesToLine,
  verticesToPolygon,
} from "@/lib/map-draw";
import type { GeoJSONFeature, GeoJSONGeometry, ProjectType } from "@/lib/types";
import { generateSiteSuggestions } from "@/lib/site-suggestions";
import { MAP_COLORS } from "@/lib/map-colors";
import DrawHud from "@/components/map/DrawHud";
import {
  basemapMaxZoom,
  buildOsmStyle,
  fetchTileProviders,
  rasterTileSource,
  type MapBasemap,
} from "@/lib/map-imagery";
import { type MapTool, useProjectStore } from "@/stores/projectStore";

export type { MapBasemap } from "@/lib/map-imagery";

const FLOATING_TOOLS: { id: MapTool; label: string; title: string }[] = [
  { id: "select", label: "☝", title: "Select / pan" },
  { id: "draw-polygon", label: "⬠", title: "Draw boundary polygon" },
  { id: "draw-line", label: "╱", title: "Draw alignment line" },
  { id: "measure-distance", label: "📏", title: "Measure distance" },
  { id: "measure-area", label: "▦", title: "Measure area" },
];

interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  boundary?: GeoJSONGeometry | null;
  alignment?: GeoJSONGeometry | null;
  analysisFeatures?: GeoJSONFeature[];
  onBoundaryDrawn?: (g: GeoJSONGeometry) => void;
  onAlignmentDrawn?: (g: GeoJSONGeometry) => void;
  onMapClick?: (lng: number, lat: number) => void;
  onSuggestionApplied?: (kind: "boundary" | "alignment", geometry: GeoJSONGeometry) => void;
  projectType?: ProjectType;
  roadFeatures?: GeoJSONFeature[];
  buildingFeatures?: GeoJSONFeature[];
  hideFloatingTools?: boolean;
  basemap?: MapBasemap;
  showCenterMarker?: boolean;
}

function pxToMeters(map: MlMap, px: number, lngLat: [number, number]): number {
  const p1 = map.project(lngLat);
  const p2 = { x: p1.x + px, y: p1.y };
  const ll2 = map.unproject([p2.x, p2.y]);
  return haversineM(lngLat, [ll2.lng, ll2.lat]);
}

export default function MapView({
  center = [77.5946, 12.9716],
  zoom = 13,
  boundary,
  alignment,
  analysisFeatures,
  onBoundaryDrawn,
  onAlignmentDrawn,
  onMapClick,
  onSuggestionApplied,
  projectType = "flyover",
  roadFeatures,
  buildingFeatures,
  hideFloatingTools = false,
  basemap = "satellite",
  showCenterMarker = false,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const basemapRef = useRef(basemap);
  const centerRef = useRef(center);
  const zoomRef = useRef(zoom);
  const boundaryRef = useRef(boundary);
  const alignmentRef = useRef(alignment);
  const draggingHandleRef = useRef<number | null>(null);
  const satelliteMaxZoomRef = useRef(22);
  const [ready, setReady] = useState(false);

  const activeTool = useProjectStore((s) => s.activeTool);
  const layers = useProjectStore((s) => s.layers);
  const siteSuggestions = useProjectStore((s) => s.siteSuggestions);
  const highlightedSuggestionId = useProjectStore((s) => s.highlightedSuggestionId);
  const vertices = useProjectStore((s) => s.drawVertices);
  const editVertices = useProjectStore((s) => s.editVertices);
  const corridorWidthM = useProjectStore((s) => s.corridorWidthM);
  const snapEnabled = useProjectStore((s) => s.snapEnabled);
  const snapRadiusPx = useProjectStore((s) => s.snapRadiusPx);
  const pendingSave = useProjectStore((s) => s.pendingSave);

  useEffect(() => {
    basemapRef.current = basemap;
  }, [basemap]);

  useEffect(() => {
    centerRef.current = center;
    zoomRef.current = zoom;
    boundaryRef.current = boundary;
    alignmentRef.current = alignment;
  }, [center, zoom, boundary, alignment]);

  const verticesRef = useRef(vertices);
  const toolRef = useRef(activeTool);
  const siteSuggestionsRef = useRef(siteSuggestions);
  const roadFeaturesRef = useRef(roadFeatures);
  const buildingFeaturesRef = useRef(buildingFeatures);
  const analysisFeaturesRef = useRef(analysisFeatures);
  const corridorWidthRef = useRef(corridorWidthM);
  const snapEnabledRef = useRef(snapEnabled);
  const snapRadiusRef = useRef(snapRadiusPx);
  const editVerticesRef = useRef(editVertices);
  const boundaryPropRef = useRef(boundary);
  const alignmentPropRef = useRef(alignment);

  useEffect(() => {
    verticesRef.current = vertices;
  }, [vertices]);
  useEffect(() => {
    toolRef.current = activeTool;
  }, [activeTool]);
  useEffect(() => {
    siteSuggestionsRef.current = siteSuggestions;
  }, [siteSuggestions]);
  useEffect(() => {
    roadFeaturesRef.current = roadFeatures;
  }, [roadFeatures]);
  useEffect(() => {
    buildingFeaturesRef.current = buildingFeatures;
  }, [buildingFeatures]);
  useEffect(() => {
    analysisFeaturesRef.current = analysisFeatures;
  }, [analysisFeatures]);
  useEffect(() => {
    corridorWidthRef.current = corridorWidthM;
  }, [corridorWidthM]);
  useEffect(() => {
    snapEnabledRef.current = snapEnabled;
  }, [snapEnabled]);
  useEffect(() => {
    snapRadiusRef.current = snapRadiusPx;
  }, [snapRadiusPx]);
  useEffect(() => {
    editVerticesRef.current = editVertices;
  }, [editVertices]);
  useEffect(() => {
    boundaryPropRef.current = boundary;
    alignmentPropRef.current = alignment;
  }, [boundary, alignment]);

  const setVertices = useCallback((v: [number, number][] | ((prev: [number, number][]) => [number, number][])) => {
    if (typeof v === "function") {
      useProjectStore.getState().setDrawVertices(v(useProjectStore.getState().drawVertices));
    } else {
      useProjectStore.getState().setDrawVertices(v);
    }
  }, []);

  const snapLngLat = useCallback((map: MlMap, lngLat: [number, number]): [number, number] => {
    if (!snapEnabledRef.current) return lngLat;
    const maxM = pxToMeters(map, snapRadiusRef.current, lngLat);
    const roadHits = (roadFeaturesRef.current ?? []).length
      ? roadFeaturesRef.current!
      : (analysisFeaturesRef.current ?? []).filter((f) => f.properties?.category === "road");
    const boundaryVerts = geometryToVertices(boundaryPropRef.current);
    const editVerts = editVerticesRef.current;
    const cornerFeatures: GeoJSONFeature[] = [...boundaryVerts, ...editVerts].map((c, i) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: c },
      properties: { id: i },
    }));
    return snapPointToFeatures(lngLat, [...roadHits, ...cornerFeatures], maxM);
  }, []);

  const queueBoundarySave = useCallback((g: GeoJSONGeometry) => {
    useProjectStore.getState().setPendingSave({ kind: "boundary", geometry: g });
    setVertices([]);
  }, [setVertices]);

  const queueAlignmentSave = useCallback((g: GeoJSONGeometry) => {
    useProjectStore.getState().setPendingSave({ kind: "alignment", geometry: g });
    setVertices([]);
  }, [setVertices]);

  const finishDraw = useCallback(() => {
    const tool = toolRef.current;
    const v = verticesRef.current;
    if (tool === "draw-polygon" && v.length >= 3) {
      queueBoundarySave(verticesToPolygon(v));
    } else if (tool === "draw-line" && v.length >= 2) {
      queueAlignmentSave(verticesToLine(v));
    } else if (tool === "draw-corridor" && v.length >= 2) {
      const poly = corridorFromLine(v, corridorWidthRef.current);
      if (poly) queueBoundarySave(poly);
    } else if (tool === "measure-area" && v.length >= 3) {
      const area = formatAreaForUnit(polygonAreaSqm(v), useProjectStore.getState().measureUnit);
      useProjectStore.getState().pushMeasureHistory({ kind: "area", value: area });
    } else if (tool === "measure-distance" && v.length >= 2) {
      const dist = formatDistanceForUnit(lineLengthM(v), useProjectStore.getState().measureUnit);
      useProjectStore.getState().pushMeasureHistory({ kind: "distance", value: dist });
    }
  }, [queueAlignmentSave, queueBoundarySave]);

  const handleConfirmSave = useCallback(() => {
    const pending = useProjectStore.getState().pendingSave;
    if (!pending) return;
    if (pending.kind === "boundary") onBoundaryDrawn?.(pending.geometry);
    else onAlignmentDrawn?.(pending.geometry);
    useProjectStore.getState().setPendingSave(null);
    useProjectStore.getState().setActiveTool("select");
  }, [onAlignmentDrawn, onBoundaryDrawn]);

  // Init edit mode when tool activates
  useEffect(() => {
    if (activeTool === "edit-boundary" && boundary) {
      useProjectStore.getState().initEditFromGeometry(boundary);
    } else if (activeTool === "edit-alignment" && alignment) {
      useProjectStore.getState().initEditFromGeometry(alignment);
    }
  }, [activeTool, boundary, alignment]);

  // --- map init ---
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    let cancelled = false;
    let disposeMap: (() => void) | undefined;

    void (async () => {
      const esriSatellite = rasterTileSource({
        provider: "esri",
        max_zoom: 22,
        tile_size: 256,
        url_template:
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attribution: "Esri World Imagery",
      });
      const esriTerrain = rasterTileSource({
        provider: "esri",
        max_zoom: 17,
        tile_size: 256,
        url_template:
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attribution: "Esri World Topo",
      });
      let style = buildOsmStyle(esriSatellite, esriTerrain);
      try {
        const providers = await fetchTileProviders();
        if (cancelled) return;
        satelliteMaxZoomRef.current = providers.satellite_config.max_zoom;
        style = buildOsmStyle(
          rasterTileSource(providers.satellite_config),
          rasterTileSource(providers.terrain_config),
        );
      } catch {
        /* use Esri fallback style */
      }
      if (cancelled || !containerRef.current || mapRef.current) return;

      const map = new maplibregl.Map({
        container: containerRef.current,
        style,
        center,
        zoom,
        maxZoom: basemapMaxZoom(basemapRef.current, satelliteMaxZoomRef.current),
        canvasContextAttributes: { preserveDrawingBuffer: true },
      });
      map.addControl(new maplibregl.NavigationControl(), "top-right");
      map.doubleClickZoom.disable();

    const publishCursor = (lngLat?: maplibregl.LngLat | null) => {
      const c = map.getCenter();
      useProjectStore.getState().setMapCursor({
        lngLat: lngLat ? [lngLat.lng, lngLat.lat] : null,
        zoom: map.getZoom(),
        bearing: map.getBearing(),
        scaleLabel: mapScaleLabel(c.lat, map.getZoom()),
      });
    };

    const bindControls = () => {
      useProjectStore.getState().setMapControls({
        zoomIn: () => map.zoomIn(),
        zoomOut: () => map.zoomOut(),
        flyHome: () => {
          const c = centerRef.current;
          map.flyTo({ center: c, zoom: zoomRef.current, bearing: 0, pitch: 0 });
        },
        resetNorth: () => map.easeTo({ bearing: 0, pitch: 0, duration: 400 }),
        fitToProject: () => {
          const bounds = bboxFromGeometries(
            boundaryRef.current ?? undefined,
            alignmentRef.current ?? undefined,
          );
          if (bounds) {
            map.fitBounds(bounds, { padding: 48, duration: 600, maxZoom: 20 });
          } else {
            const c = centerRef.current;
            map.flyTo({ center: c, zoom: zoomRef.current, bearing: 0, pitch: 0 });
          }
        },
        exportPng: () => {
          try {
            const canvas = map.getCanvas();
            const link = document.createElement("a");
            link.download = `map-${Date.now()}.png`;
            link.href = canvas.toDataURL("image/png");
            link.click();
            return true;
          } catch {
            return false;
          }
        },
        getViewport: () => ({
          center: [map.getCenter().lng, map.getCenter().lat],
          zoom: map.getZoom(),
          bearing: map.getBearing(),
          pitch: map.getPitch(),
        }),
        flyToViewport: (v) => {
          map.flyTo({
            center: v.center,
            zoom: v.zoom,
            bearing: v.bearing,
            pitch: v.pitch,
            duration: 800,
          });
        },
      });
    };

    const onMove = () => publishCursor();
    const onMouseMove = (e: maplibregl.MapMouseEvent) => publishCursor(e.lngLat);
    const onMouseOut = () => publishCursor(null);

    publishCursor();
    map.on("move", onMove);
    map.on("mousemove", onMouseMove);
    map.on("mouseout", onMouseOut);
    map.on("load", () => {
      map.addSource("draft", { type: "geojson", data: emptyFC() });
      map.addLayer({
        id: "draft-line",
        type: "line",
        source: "draft",
        paint: { "line-color": MAP_COLORS.primary, "line-width": 2, "line-dasharray": [2, 1] },
      });
      map.addLayer({
        id: "draft-fill",
        type: "fill",
        source: "draft",
        paint: { "fill-color": MAP_COLORS.primary, "fill-opacity": 0.12 },
        filter: ["==", ["geometry-type"], "Polygon"],
      });
      map.addSource("saved", { type: "geojson", data: emptyFC() });
      map.addLayer({
        id: "saved-fill",
        type: "fill",
        source: "saved",
        paint: { "fill-color": MAP_COLORS.valid, "fill-opacity": 0.15 },
        filter: ["==", ["geometry-type"], "Polygon"],
      });
      map.addLayer({
        id: "saved-line",
        type: "line",
        source: "saved",
        paint: { "line-color": MAP_COLORS.valid, "line-width": 2.5 },
      });
      map.addSource("edit-handles", { type: "geojson", data: emptyFC() });
      map.addLayer({
        id: "edit-handles-circle",
        type: "circle",
        source: "edit-handles",
        paint: {
          "circle-radius": ["case", ["boolean", ["get", "midpoint"], false], 4, 7],
          "circle-color": MAP_COLORS.primary,
          "circle-stroke-width": 2,
          "circle-stroke-color": MAP_COLORS.vertexStroke,
        },
      });
      map.addSource("analysis", { type: "geojson", data: emptyFC() });
      map.addLayer({
        id: "analysis-roads",
        type: "line",
        source: "analysis",
        paint: { "line-color": MAP_COLORS.road, "line-width": 2 },
        filter: ["==", ["get", "category"], "road"],
      });
      map.addSource("suggestions", { type: "geojson", data: emptyFC() });
      map.addLayer({
        id: "suggestions-fill",
        type: "fill",
        source: "suggestions",
        paint: {
          "fill-color": ["case", ["get", "highlighted"], MAP_COLORS.primary, MAP_COLORS.structure],
          "fill-opacity": ["case", ["get", "highlighted"], 0.35, 0.18],
        },
        filter: ["==", ["geometry-type"], "Polygon"],
      });
      map.addLayer({
        id: "suggestions-line",
        type: "line",
        source: "suggestions",
        paint: {
          "line-color": ["case", ["get", "highlighted"], MAP_COLORS.primary, MAP_COLORS.structure],
          "line-width": ["case", ["get", "highlighted"], 3, 2],
          "line-dasharray": [2, 1],
        },
      });
      map.addLayer({
        id: "analysis-buildings",
        type: "fill",
        source: "analysis",
        paint: { "fill-color": "#6E7D91", "fill-opacity": 0.25 },
        filter: ["==", ["get", "category"], "building"],
      });
      map.addLayer({
        id: "analysis-water",
        type: "line",
        source: "analysis",
        paint: { "line-color": MAP_COLORS.water, "line-width": 2 },
        filter: ["==", ["get", "category"], "waterway"],
      });
      applyBasemapVisibility(map, basemapRef.current);
      applyOverlayVisibility(map, useProjectStore.getState().layers);
      bindControls();
      setReady(true);
      useProjectStore.getState().setMapReady(true);
    });
    mapRef.current = map;
    const container = containerRef.current;
    if (!container) {
      map.remove();
      mapRef.current = null;
      return;
    }
    const ro = new ResizeObserver(() => {
      try {
        map.resize();
      } catch {
        /* map not ready yet */
      }
    });
    ro.observe(container);
    disposeMap = () => {
      ro.disconnect();
      map.off("move", onMove);
      map.off("mousemove", onMouseMove);
      map.off("mouseout", onMouseOut);
      useProjectStore.getState().setMapControls(null);
      useProjectStore.getState().setMapCursor(null);
      useProjectStore.getState().setMapReady(false);
      map.remove();
      mapRef.current = null;
      setReady(false);
    };
    })();

    return () => {
      cancelled = true;
      disposeMap?.();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- click / dblclick / keyboard ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    const onClick = (e: maplibregl.MapMouseEvent) => {
      const tool = toolRef.current;
      let lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      lngLat = snapLngLat(map, lngLat);

      if (tool === "suggest-site") {
        const list = generateSiteSuggestions(
          lngLat[0],
          lngLat[1],
          projectType,
          roadFeaturesRef.current ?? [],
        );
        const store = useProjectStore.getState();
        store.setSiteSuggestions(list);
        store.setHighlightedSuggestionId(list[0]?.id ?? null);
        store.setActiveTool("select");
        return;
      }

      const suggestionHits = map.queryRenderedFeatures(e.point, {
        layers: ["suggestions-fill", "suggestions-line"],
      });
      if (suggestionHits.length > 0) {
        const props = suggestionHits[0].properties as { id?: string; kind?: string };
        const hit = siteSuggestionsRef.current.find((s) => s.id === props?.id);
        if (hit) {
          onSuggestionApplied?.(hit.kind, hit.geometry);
          return;
        }
      }

      if (tool === "select") {
        const buildingHits = map.queryRenderedFeatures(e.point, { layers: ["analysis-buildings"] });
        if (buildingHits.length > 0 && buildingHits[0].geometry.type === "Polygon") {
          queueBoundarySave(buildingHits[0].geometry as GeoJSONGeometry);
          return;
        }
        onMapClick?.(lngLat[0], lngLat[1]);
        return;
      }

      if (tool === "edit-boundary" || tool === "edit-alignment") return;

      if (tool === "draw-rectangle") {
        const v = verticesRef.current;
        if (v.length === 0) {
          useProjectStore.getState().pushDrawVertex(lngLat);
        } else if (v.length === 1) {
          queueBoundarySave(rectangleFromCorners(v[0], lngLat));
        }
        return;
      }

      useProjectStore.getState().pushDrawVertex(lngLat);
    };

    const onDblClick = (e: maplibregl.MapMouseEvent) => {
      const tool = toolRef.current;
      e.preventDefault();
      if (tool === "draw-polygon" || tool === "draw-line" || tool === "draw-corridor") {
        finishDraw();
      }
    };

    const onKeyDown = (e: KeyboardEvent) => {
      const tool = toolRef.current;
      if (e.key === "Escape") {
        setVertices([]);
        useProjectStore.getState().setPendingSave(null);
        if (tool.startsWith("measure")) useProjectStore.getState().setActiveTool("select");
        return;
      }
      if (e.key === "Backspace") {
        useProjectStore.getState().popDrawVertex();
        return;
      }
      if (e.key === "Enter") {
        if (
          tool === "draw-polygon" ||
          tool === "draw-line" ||
          tool === "draw-corridor" ||
          tool === "measure-area"
        ) {
          finishDraw();
        }
      }
    };

    map.on("click", onClick);
    map.on("dblclick", onDblClick);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      map.off("click", onClick);
      map.off("dblclick", onDblClick);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [
    ready,
    onMapClick,
    onSuggestionApplied,
    projectType,
    setVertices,
    snapLngLat,
    finishDraw,
    queueBoundarySave,
  ]);

  // --- edit handle drag ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    const onMouseDown = (e: maplibregl.MapMouseEvent) => {
      const tool = toolRef.current;
      if (tool !== "edit-boundary" && tool !== "edit-alignment") return;
      const hits = map.queryRenderedFeatures(e.point, { layers: ["edit-handles-circle"] });
      if (!hits.length) return;
      const properties = hits[0].properties as { index?: number; midpoint?: boolean };
      const idx = properties?.index;
      if (idx == null) return;
      const current = [...editVerticesRef.current];
      if (e.originalEvent.altKey && !properties.midpoint) {
        if (current.length > (tool === "edit-boundary" ? 3 : 2)) {
          current.splice(idx, 1);
          useProjectStore.getState().setEditVertices(current);
        }
        e.preventDefault();
        return;
      }
      if (properties.midpoint) {
        current.splice(idx, 0, [e.lngLat.lng, e.lngLat.lat]);
        editVerticesRef.current = current;
        useProjectStore.getState().setEditVertices(current);
      }
      draggingHandleRef.current = idx;
      map.dragPan.disable();
      e.preventDefault();
    };

    const onMouseMove = (e: maplibregl.MapMouseEvent) => {
      const idx = draggingHandleRef.current;
      if (idx == null) return;
      let lngLat: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      lngLat = snapLngLat(map, lngLat);
      const verts = [...editVerticesRef.current];
      verts[idx] = lngLat;
      useProjectStore.getState().setEditVertices(verts);
    };

    const onMouseUp = () => {
      if (draggingHandleRef.current != null) {
        draggingHandleRef.current = null;
        map.dragPan.enable();
      }
    };

    map.on("mousedown", onMouseDown);
    map.on("mousemove", onMouseMove);
    map.on("mouseup", onMouseUp);
    return () => {
      draggingHandleRef.current = null;
      map.dragPan.enable();
      map.off("mousedown", onMouseDown);
      map.off("mousemove", onMouseMove);
      map.off("mouseup", onMouseUp);
    };
  }, [ready, snapLngLat]);

  // --- draft rendering ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (activeTool === "edit-boundary" || activeTool === "edit-alignment") return;
    const src = map.getSource("draft") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    const features: GeoJSON.Feature[] = [];
    const pending = useProjectStore.getState().pendingSave;
    if (pending) {
      features.push({ type: "Feature", geometry: pending.geometry as GeoJSON.Geometry, properties: {} });
    } else if (vertices.length >= 2) {
      if (activeTool === "draw-corridor") {
        const poly = corridorFromLine(vertices, corridorWidthM);
        if (poly) features.push({ type: "Feature", geometry: poly as GeoJSON.Geometry, properties: {} });
        features.push({
          type: "Feature",
          geometry: { type: "LineString", coordinates: vertices },
          properties: {},
        });
      } else if (
        (activeTool === "draw-polygon" || activeTool === "measure-area") &&
        vertices.length >= 3
      ) {
        features.push({
          type: "Feature",
          geometry: { type: "Polygon", coordinates: [[...vertices, vertices[0]]] },
          properties: {},
        });
      } else if (activeTool === "draw-rectangle" && vertices.length === 1) {
        features.push({
          type: "Feature",
          geometry: { type: "LineString", coordinates: vertices },
          properties: {},
        });
      } else if (activeTool === "draw-rectangle" && vertices.length >= 2) {
        features.push({
          type: "Feature",
          geometry: rectangleFromCorners(vertices[0], vertices[1]) as GeoJSON.Geometry,
          properties: {},
        });
      } else {
        features.push({
          type: "Feature",
          geometry: { type: "LineString", coordinates: vertices },
          properties: {},
        });
      }
    }
    src.setData({ type: "FeatureCollection", features });
  }, [vertices, activeTool, ready, corridorWidthM, pendingSave]);

  // --- edit handles ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const src = map.getSource("edit-handles") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    const isEdit = activeTool === "edit-boundary" || activeTool === "edit-alignment";
    if (!isEdit) {
      src.setData(emptyFC());
      return;
    }
    src.setData({
      type: "FeatureCollection",
      features: [...editVertices.map((c, index) => ({
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: c },
        properties: { index, midpoint: false },
      })), ...editVertices.flatMap((c, index) => {
        const next = editVertices[index + 1] ?? (activeTool === "edit-boundary" ? editVertices[0] : null);
        if (!next) return [];
        return [{ type: "Feature" as const, geometry: { type: "Point" as const, coordinates: [(c[0] + next[0]) / 2, (c[1] + next[1]) / 2] }, properties: { index: index + 1, midpoint: true } }];
      })],
    });
    const editSrc = map.getSource("draft") as maplibregl.GeoJSONSource | undefined;
    if (editSrc) {
      const geom =
        activeTool === "edit-boundary"
          ? verticesToPolygon(editVertices)
          : verticesToLine(editVertices);
      editSrc.setData({
        type: "FeatureCollection",
        features: [{ type: "Feature", geometry: geom as GeoJSON.Geometry, properties: {} }],
      });
    }
  }, [editVertices, activeTool, ready]);

  // --- saved geometry rendering ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const isEdit = activeTool === "edit-boundary" || activeTool === "edit-alignment";
    const src = map.getSource("saved") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    const features: GeoJSON.Feature[] = [];
    if (boundary && activeTool !== "edit-boundary")
      features.push({ type: "Feature", geometry: boundary as GeoJSON.Geometry, properties: {} });
    if (alignment && activeTool !== "edit-alignment")
      features.push({ type: "Feature", geometry: alignment as GeoJSON.Geometry, properties: {} });
    src.setData({ type: "FeatureCollection", features: isEdit ? [] : features });
  }, [boundary, alignment, ready, activeTool]);

  // --- analysis layers ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const src = map.getSource("analysis") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    src.setData({
      type: "FeatureCollection",
      features: (analysisFeatures ?? []) as GeoJSON.Feature[],
    });
  }, [analysisFeatures, ready]);

  // --- site suggestion overlays ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const src = map.getSource("suggestions") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    src.setData({
      type: "FeatureCollection",
      features: siteSuggestions.map((s) => ({
        type: "Feature" as const,
        geometry: s.geometry as GeoJSON.Geometry,
        properties: {
          id: s.id,
          kind: s.kind,
          label: s.label,
          score: s.score,
          highlighted: s.id === highlightedSuggestionId,
        },
      })),
    });
  }, [siteSuggestions, highlightedSuggestionId, ready]);

  // --- basemap ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    map.setMaxZoom(basemapMaxZoom(basemap, satelliteMaxZoomRef.current));
    applyBasemapVisibility(map, basemap);
  }, [basemap, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    applyOverlayVisibility(map, layers);
  }, [layers, ready]);

  // --- cursor style ---
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const drawTools = [
      "draw-polygon",
      "draw-line",
      "draw-rectangle",
      "draw-corridor",
      "measure-distance",
      "measure-area",
    ];
    if (drawTools.includes(activeTool)) el.style.cursor = "crosshair";
    else if (activeTool === "edit-boundary" || activeTool === "edit-alignment") el.style.cursor = "grab";
    else el.style.cursor = "";
  }, [activeTool]);

  // --- recenter ---
  useEffect(() => {
    mapRef.current?.flyTo({ center, zoom });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center[0], center[1]]);

  const selectTool = useCallback(
    (t: MapTool) => {
      setVertices([]);
      useProjectStore.getState().activateTool(t);
    },
    [setVertices],
  );

  return (
    <div className="relative w-full h-full bg-background">
      <div ref={containerRef} className="absolute inset-0 maplibre-canvas-host" />
      {showCenterMarker && (
        <div className="pointer-events-none absolute inset-0 z-[5] flex items-center justify-center">
          <div className="relative h-8 w-8">
            <div className="absolute inset-0 rounded-full border-2 border-primary/60 shadow-[var(--shadow-glow-cyan)]" />
            <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-primary/70" />
            <div className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-primary/70" />
          </div>
        </div>
      )}
      {!hideFloatingTools && (
        <div className="absolute top-2 left-2 z-10 flex flex-col gap-1 panel p-1">
          {FLOATING_TOOLS.map((t) => (
            <button
              key={t.id}
              title={t.title}
              onClick={() => selectTool(t.id)}
              className={`w-8 h-8 text-sm flex items-center justify-center hover:bg-muted ${
                activeTool === t.id ? "bg-primary/15 text-primary" : "text-muted-foreground"
              }`}
            >
              {t.label}
            </button>
          ))}
          <button
            title="Clear selection"
            onClick={() => {
              setVertices([]);
              useProjectStore.getState().setActiveTool("select");
            }}
            className="w-8 h-8 text-sm flex items-center justify-center hover:bg-muted text-muted-foreground"
          >
            ✕
          </button>
        </div>
      )}
      <DrawHud onConfirmSave={handleConfirmSave} />
      {activeTool === "suggest-site" && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 z-10 panel-glass rounded-md px-3 py-1.5 text-xs text-accent border border-accent/30 pointer-events-none">
          {toolInstruction("suggest-site")}
        </div>
      )}
      {siteSuggestions.length > 0 && activeTool === "select" && (
        <div className="absolute bottom-14 left-2 z-10 panel-glass rounded-md px-3 py-1.5 text-[10px] text-muted-foreground max-w-[220px]">
          {siteSuggestions.length} suggestions on map — click a shape to apply · click building for boundary
        </div>
      )}
    </div>
  );
}

function emptyFC(): GeoJSON.FeatureCollection {
  return { type: "FeatureCollection", features: [] };
}

function whenMapStyleReady(map: MlMap, fn: () => void): () => void {
  let cancelled = false;
  const run = () => {
    if (cancelled) return;
    try {
      if (!map.isStyleLoaded()) {
        map.once("idle", run);
        return;
      }
      fn();
    } catch {
      map.once("idle", run);
    }
  };
  map.once("idle", run);
  return () => {
    cancelled = true;
  };
}

function applyBasemapVisibility(map: MlMap, basemap: MapBasemap) {
  const vis = (on: boolean) => (on ? "visible" : "none");
  whenMapStyleReady(map, () => {
    if (map.getLayer("osm")) map.setLayoutProperty("osm", "visibility", vis(basemap === "street"));
    if (map.getLayer("satellite"))
      map.setLayoutProperty("satellite", "visibility", vis(basemap === "satellite"));
    if (map.getLayer("topo")) map.setLayoutProperty("topo", "visibility", vis(basemap === "terrain"));
  });
}

function applyOverlayVisibility(
  map: MlMap,
  layers: { roads: boolean; buildings: boolean },
) {
  const vis = (on: boolean) => (on ? "visible" : "none");
  whenMapStyleReady(map, () => {
    if (map.getLayer("analysis-roads"))
      map.setLayoutProperty("analysis-roads", "visibility", vis(layers.roads));
    if (map.getLayer("analysis-buildings"))
      map.setLayoutProperty("analysis-buildings", "visibility", vis(layers.buildings));
  });
}
