"use client";

import type maplibregl from "maplibre-gl";
import { useMemo, useState } from "react";
import DeckOverlay from "@/components/map/DeckOverlay";
import DrawingTools from "@/components/map/DrawingTools";
import FeaturePropertiesPanel from "@/components/map/FeaturePropertiesPanel";
import MapLibreBaseMap from "@/components/map/MapLibreBaseMap";
import MapStatusBar from "@/components/map/MapStatusBar";
import MapToolbar from "@/components/map/MapToolbar";
import LiveGenerationPreview from "@/components/workspace/LiveGenerationPreview";
import type {
  WorkspaceDrawTool,
  WorkspaceFeature,
  WorkspaceFeatureCollection,
  WorkspaceMapStatus,
  WorkspaceMapStyle,
} from "@/components/map/mapTypes";
import type { GeoJSONGeometry, Project } from "@/lib/types";
import { asFeatureCollection, mergeProjectFeatures } from "@/lib/map/geojson";
import { getProviderStatus } from "@/lib/map/providers";
import { setTerrainEnabled, terrainAvailable } from "@/lib/map/terrain";

interface MapLibreWorkspaceProps {
  project: Project;
  modelUrl?: string | null;
  excavationUrl?: string | null;
  onBoundaryDrawn?: (g: GeoJSONGeometry) => void;
  onAlignmentDrawn?: (g: GeoJSONGeometry) => void;
  onLocationChange?: (lng: number, lat: number, name: string) => void | Promise<void>;
  onGenerate?: () => void;
  onAnalyze?: () => void;
  onGenerationCompleted?: () => void;
}

const DEFAULT_STATUS: WorkspaceMapStatus = {
  lngLat: null,
  zoom: 15,
  pitch: 58,
  bearing: -18,
};

export default function MapLibreWorkspace({
  project,
  modelUrl,
}: MapLibreWorkspaceProps) {
  const projectCenter: [number, number] = [
    project.center_lng ?? 77.5946,
    project.center_lat ?? 12.9716,
  ];
  const providerStatus = useMemo(() => getProviderStatus(), []);
  const [map, setMap] = useState<maplibregl.Map | null>(null);
  const [mapStyle, setMapStyle] = useState<WorkspaceMapStyle>("dark");
  const [activeTool, setActiveTool] = useState<WorkspaceDrawTool>("select");
  const [features, setFeatures] = useState<WorkspaceFeatureCollection>(() =>
    mergeProjectFeatures(project.boundary_geojson, project.alignment_geojson),
  );
  const [selectedFeature, setSelectedFeature] = useState<WorkspaceFeature | null>(null);
  const [status, setStatus] = useState<WorkspaceMapStatus>(DEFAULT_STATUS);
  const [terrainEnabled, setTerrainState] = useState(false);
  const [terrainMessage, setTerrainMessage] = useState<string | null>(null);
  const [google3dEnabled, setGoogle3dEnabled] = useState(false);
  const [buildingsEnabled, setBuildingsEnabled] = useState(true);
  const [aiPlaceholderEnabled] = useState(true);
  const [drawingError, setDrawingError] = useState<string | null>(null);
  const [deleteSignal, setDeleteSignal] = useState(0);

  const selectedId = selectedFeature?.properties.id ?? null;
  const warning = terrainMessage ?? providerStatus.warnings[0] ?? null;

  const updateFeatureName = (name: string) => {
    if (!selectedFeature) return;
    const next = {
      ...selectedFeature,
      properties: { ...selectedFeature.properties, name },
    };
    setSelectedFeature(next);
    setFeatures((current) =>
      asFeatureCollection(
        current.features.map((feature) =>
          feature.properties.id === selectedFeature.properties.id ? next : feature,
        ),
      ),
    );
  };

  const requestDeleteSelected = () => {
    if (!selectedFeature) return;
    setDeleteSignal((value) => value + 1);
    setFeatures((current) =>
      asFeatureCollection(
        current.features.filter((feature) => feature.properties.id !== selectedFeature.properties.id),
      ),
    );
    setSelectedFeature(null);
  };

  const toggleTerrain = () => {
    if (!map) return;
    const next = !terrainEnabled;
    const result = setTerrainEnabled(map, next, 1.5);
    if (!result.ok) {
      setTerrainMessage(result.message);
      setTerrainState(false);
      return;
    }
    setTerrainMessage(null);
    setTerrainState(next);
  };

  const exportFeatures = () => {
    const blob = new Blob([JSON.stringify(features, null, 2)], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `geoai-project-${project.id}-workspace.geojson`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const resetView = () => {
    map?.flyTo({ center: projectCenter, zoom: 15, pitch: 58, bearing: -18, essential: true });
  };

  return (
    <div className="absolute inset-0 overflow-hidden bg-background">
      <MapLibreBaseMap
        center={projectCenter}
        zoom={15}
        mapStyle={mapStyle}
        onMapReady={setMap}
        onStatusChange={setStatus}
      />

      <DeckOverlay
        map={map}
        features={features}
        selectedId={selectedId}
        google3dEnabled={google3dEnabled && providerStatus.googleMapsKey}
        aiPlaceholderEnabled={aiPlaceholderEnabled}
        modelUrl={modelUrl}
        modelCenter={projectCenter}
        modelAlignment={project.alignment_geojson}
      />

      <MapToolbar
        mapStyle={mapStyle}
        onMapStyleChange={setMapStyle}
        terrainEnabled={terrainEnabled}
        onTerrainToggle={toggleTerrain}
        terrainDisabled={!terrainAvailable()}
        google3dEnabled={google3dEnabled}
        onGoogle3dToggle={() => setGoogle3dEnabled((value) => !value)}
        google3dDisabled={!providerStatus.googleMapsKey}
        buildingsEnabled={buildingsEnabled}
        onBuildingsToggle={() => setBuildingsEnabled((value) => !value)}
        onExport={exportFeatures}
        onResetView={resetView}
        warning={warning}
      />

      <DrawingTools
        map={map}
        activeTool={activeTool}
        onActiveToolChange={setActiveTool}
        features={features}
        onFeaturesChange={setFeatures}
        selectedFeature={selectedFeature}
        onSelectedFeatureChange={setSelectedFeature}
        deleteSignal={deleteSignal}
        onError={setDrawingError}
      />

      <FeaturePropertiesPanel
        feature={selectedFeature}
        onRename={updateFeatureName}
        onDelete={requestDeleteSelected}
      />

      <MapStatusBar
        status={status}
        selectedFeature={selectedFeature}
        providerStatus={providerStatus}
        drawingError={drawingError}
      />

      <LiveGenerationPreview map={map} project={project} />

      {!providerStatus.googleMapsKey && (
        <div className="pointer-events-none absolute bottom-20 right-4 z-20 max-w-sm rounded-2xl border border-[rgba(245,158,11,0.22)] bg-[rgba(5,7,10,0.78)] px-3 py-2 text-[11px] leading-snug text-[#FCD34D] shadow-xl backdrop-blur-xl">
          Google Photorealistic 3D Tiles are disabled until NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is configured.
        </div>
      )}
    </div>
  );
}
