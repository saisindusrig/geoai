"use client";

import type maplibregl from "maplibre-gl";
import {
  Download,
  Eraser,
  FileUp,
  MapPin,
  MousePointer2,
  Pentagon,
  RectangleHorizontal,
  Route,
  Trash2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  TerraDraw,
  TerraDrawLineStringMode,
  TerraDrawPointMode,
  TerraDrawPolygonMode,
  TerraDrawRectangleMode,
  TerraDrawSelectMode,
  type GeoJSONStoreFeatures,
  type GeoJSONStoreGeometries,
} from "terra-draw";
import { TerraDrawMapLibreGLAdapter } from "terra-draw-maplibre-gl-adapter";
import type { WorkspaceDrawTool, WorkspaceFeature, WorkspaceFeatureCollection } from "@/components/map/mapTypes";
import { asFeatureCollection, enrichFeature, parseFeatureCollection } from "@/lib/map/geojson";
import { cn } from "@/lib/utils";

const TOOL_TO_MODE: Partial<Record<WorkspaceDrawTool, string>> = {
  select: "select",
  point: "point",
  road: "linestring",
  polygon: "polygon",
  rectangle: "rectangle",
};

const TOOLS: {
  id: WorkspaceDrawTool;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { id: "select", label: "Select", icon: MousePointer2 },
  { id: "point", label: "Point", icon: MapPin },
  { id: "road", label: "Draw Road", icon: Route },
  { id: "polygon", label: "Draw Area", icon: Pentagon },
  { id: "rectangle", label: "Rectangle", icon: RectangleHorizontal },
  { id: "delete", label: "Delete", icon: Trash2 },
];

function safeStopDraw(draw: TerraDraw | null) {
  if (!draw) return;
  try {
    draw.stop();
  } catch (error) {
    console.warn("[sitegeoai] Terra Draw cleanup skipped after MapLibre teardown", error);
  }
}

function safeClearDraw(draw: TerraDraw | null) {
  if (!draw) return;
  try {
    draw.clear();
  } catch (error) {
    console.warn("[sitegeoai] Terra Draw clear failed after MapLibre teardown", error);
  }
}

function fromTerraFeature(feature: GeoJSONStoreFeatures<GeoJSONStoreGeometries>): WorkspaceFeature | null {
  if (!["Point", "LineString", "Polygon"].includes(feature.geometry.type)) return null;
  const existing = feature.properties ?? {};
  const kind =
    feature.geometry.type === "Point"
      ? "point"
      : feature.geometry.type === "LineString"
        ? "road"
        : existing.kind === "rectangle"
          ? "rectangle"
          : "area";
  return enrichFeature({
    type: "Feature",
    geometry: feature.geometry,
    properties: {
      id: String(existing.id ?? feature.id),
      name: String(existing.name ?? (kind === "road" ? "Road centerline" : kind === "point" ? "Point marker" : "Area")),
      kind,
      ...existing,
    },
  } as WorkspaceFeature);
}

interface DrawingToolsProps {
  map: maplibregl.Map | null;
  activeTool: WorkspaceDrawTool;
  onActiveToolChange: (tool: WorkspaceDrawTool) => void;
  features: WorkspaceFeatureCollection;
  onFeaturesChange: (features: WorkspaceFeatureCollection) => void;
  selectedFeature: WorkspaceFeature | null;
  onSelectedFeatureChange: (feature: WorkspaceFeature | null) => void;
  deleteSignal?: number;
  onError?: (message: string | null) => void;
}

export default function DrawingTools({
  map,
  activeTool,
  onActiveToolChange,
  features,
  onFeaturesChange,
  selectedFeature,
  onSelectedFeatureChange,
  deleteSignal,
  onError,
}: DrawingToolsProps) {
  const drawRef = useRef<TerraDraw | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const initialFeaturesRef = useRef(features.features);
  const [ready, setReady] = useState(false);

  const syncFromDraw = useCallback(() => {
    const draw = drawRef.current;
    if (!draw) return;
    const next = draw.getSnapshot().map(fromTerraFeature).filter(Boolean) as WorkspaceFeature[];
    onFeaturesChange(asFeatureCollection(next));
  }, [onFeaturesChange]);

  useEffect(() => {
    if (!map || drawRef.current) return;
    try {
      const draw = new TerraDraw({
        adapter: new TerraDrawMapLibreGLAdapter({ map }),
        modes: [
          new TerraDrawSelectMode({
            flags: {
              polygon: { feature: { draggable: true, coordinates: { draggable: true, deletable: true } } },
              linestring: { feature: { draggable: true, coordinates: { draggable: true, deletable: true } } },
              point: { feature: { draggable: true } },
            },
          }),
          new TerraDrawPointMode(),
          new TerraDrawLineStringMode({ editable: true, showCoordinatePoints: true }),
          new TerraDrawPolygonMode({ editable: true, showCoordinatePoints: true }),
          new TerraDrawRectangleMode(),
        ],
      });

      const handleFinish = () => syncFromDraw();
      const handleChange = () => syncFromDraw();
      const handleSelect = (id: string | number) => {
        const found = draw.getSnapshotFeature(id);
        onSelectedFeatureChange(found ? fromTerraFeature(found) : null);
      };
      const handleDeselect = () => onSelectedFeatureChange(null);

      draw.on("finish", handleFinish);
      draw.on("change", handleChange);
      draw.on("select", handleSelect);
      draw.on("deselect", handleDeselect);
      draw.start();
      draw.addFeatures(initialFeaturesRef.current as unknown as GeoJSONStoreFeatures<GeoJSONStoreGeometries>[]);
      drawRef.current = draw;
      queueMicrotask(() => setReady(true));
      onError?.(null);

      return () => {
        try {
          draw.off("finish", handleFinish);
          draw.off("change", handleChange);
          draw.off("select", handleSelect);
          draw.off("deselect", handleDeselect);
        } catch {
          // Terra Draw may already have unregistered during route teardown.
        }
        safeStopDraw(draw);
        drawRef.current = null;
        queueMicrotask(() => setReady(false));
      };
    } catch (error) {
      console.warn("[sitegeoai] Terra Draw initialization failed", error);
      onError?.("Drawing tools failed to initialize. Map pan/zoom remains available.");
    }
  }, [map, onError, onSelectedFeatureChange, syncFromDraw]);

  useEffect(() => {
    const draw = drawRef.current;
    const mode = TOOL_TO_MODE[activeTool];
    if (!draw || !mode) return;
    try {
      draw.setMode(mode);
    } catch (error) {
      console.warn("[sitegeoai] Could not change Terra Draw mode", error);
    }
  }, [activeTool]);

  const deleteSelected = () => {
    const draw = drawRef.current;
    if (!draw || !selectedFeature?.properties.id) return;
    try {
      draw.removeFeatures([selectedFeature.properties.id]);
    } catch (error) {
      console.warn("[sitegeoai] Terra Draw delete failed", error);
    }
    onSelectedFeatureChange(null);
    syncFromDraw();
  };

  useEffect(() => {
    if (!deleteSignal) return;
    deleteSelected();
    // deleteSelected intentionally reads the latest selected feature.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deleteSignal]);

  const clearAll = () => {
    safeClearDraw(drawRef.current);
    onSelectedFeatureChange(null);
    onFeaturesChange({ type: "FeatureCollection", features: [] });
  };

  const exportGeoJson = () => {
    const blob = new Blob([JSON.stringify(features, null, 2)], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "geoai-workspace-features.geojson";
    link.click();
    URL.revokeObjectURL(url);
  };

  const importGeoJson = async (file?: File) => {
    if (!file) return;
    const parsed = parseFeatureCollection(await file.text());
    if (!parsed) {
      onError?.("Import failed: expected a GeoJSON FeatureCollection with Point, LineString, or Polygon features.");
      return;
    }
    safeClearDraw(drawRef.current);
    try {
      drawRef.current?.addFeatures(parsed.features as unknown as GeoJSONStoreFeatures<GeoJSONStoreGeometries>[]);
    } catch (error) {
      console.warn("[sitegeoai] Terra Draw import failed", error);
    }
    onFeaturesChange(parsed);
    onError?.(null);
  };

  return (
    <div className="pointer-events-auto absolute left-4 top-24 z-30 flex flex-col gap-2">
      <div className="rounded-2xl border border-border bg-[rgba(5,7,10,0.78)] p-1.5 shadow-2xl backdrop-blur-xl">
        <div className="space-y-1">
          {TOOLS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              disabled={!ready && id !== "select"}
              onClick={() => {
                if (id === "delete") deleteSelected();
                else onActiveToolChange(id);
              }}
              title={label}
              aria-label={label}
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-xl border text-foreground-secondary transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 disabled:opacity-40",
                activeTool === id
                  ? "border-[rgba(34,211,238,0.5)] bg-[rgba(34,211,238,0.14)] text-[#A5F3FC] shadow-[0_0_18px_rgba(34,211,238,0.16)]"
                  : "border-transparent hover:border-border hover:bg-surface-hover hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
            </button>
          ))}
        </div>
      </div>
      <div className="rounded-2xl border border-border bg-[rgba(5,7,10,0.78)] p-1.5 shadow-2xl backdrop-blur-xl">
        <button
          type="button"
          onClick={clearAll}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-foreground-secondary hover:bg-surface-hover hover:text-foreground"
          title="Clear all"
        >
          <Eraser className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-foreground-secondary hover:bg-surface-hover hover:text-foreground"
          title="Import GeoJSON"
        >
          <FileUp className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={exportGeoJson}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-foreground-secondary hover:bg-surface-hover hover:text-foreground"
          title="Export GeoJSON"
        >
          <Download className="h-4 w-4" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          title="Import GeoJSON"
          aria-label="Import GeoJSON"
          accept=".json,.geojson,application/geo+json,application/json"
          className="hidden"
          onChange={(event) => void importGeoJson(event.target.files?.[0])}
        />
      </div>
    </div>
  );
}
