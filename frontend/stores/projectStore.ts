import { create } from "zustand";

import type { AccuracyTier, GeoJSONFeature, GeoJSONGeometry, GeometrySpec, JobStatus, Project } from "@/lib/types";

import type { SiteSuggestion } from "@/lib/site-suggestions";
import { extractDesignMeshLayers } from "@/lib/design-mesh-layers";
import type { Scene3DObjectInfo, Scene3DLayerKey } from "@/lib/cesium-scene";
import { defaultScene3DLayers } from "@/lib/cesium-scene";
import { defaultCorridorWidth, geometryToVertices, type ToolHint } from "@/lib/map-draw";

export type MapTool =
  | "select"
  | "draw-polygon"
  | "draw-line"
  | "draw-rectangle"
  | "draw-corridor"
  | "measure-distance"
  | "measure-area"
  | "suggest-site"
  | "edit-boundary"
  | "edit-alignment";

export type PendingSave = { kind: "boundary" | "alignment"; geometry: GeoJSONGeometry };

export type MeasureEntry = {
  id: string;
  kind: "distance" | "area";
  value: string;
  at: number;
};

export type Scene3DMeasureTool = "none" | "distance" | "area" | "height" | "slope" | "depth" | "clearance";

export type Scene3DLayerVisibility = Record<Scene3DLayerKey, boolean>;

export type MeasureUnit = "m" | "ft";

export type LayerPreset = "planning" | "analysis" | "presentation";

export interface LayerVisibility {
  satellite: boolean;
  roads: boolean;
  buildings: boolean;
  terrain: boolean;
  tiles3d: boolean;
  projectModel: boolean;
  excavation: boolean;
  utilities: boolean;
}

export interface SurveyLayerVisibility {
  visualBasemap: boolean;
  surveyOrtho: boolean;
  surveyDem: boolean;
  surveyVectors: boolean;
  surveyGcp: boolean;
}

export interface ModelLayerVisibility {
  outer: boolean;
  inner: boolean;
  foundation: boolean;
  steel: boolean;
  concrete: boolean;
  drainage: boolean;
  electrical: boolean;
  pipeline: boolean;
  traffic: boolean;
}

export interface MapViewportState {
  center: [number, number];
  zoom: number;
  bearing: number;
  pitch: number;
}

export interface MapControls {
  zoomIn?: () => void;
  zoomOut?: () => void;
  flyHome?: () => void;
  resetNorth?: () => void;
  fitToProject?: () => void;
  exportPng?: () => boolean;
  getViewport?: () => MapViewportState;
  flyToViewport?: (v: MapViewportState) => void;
}

export interface MapCursorState {
  lngLat: [number, number] | null;
  zoom: number;
  bearing: number;
  scaleLabel: string;
}

export const LAYER_PRESETS: Record<LayerPreset, Partial<LayerVisibility>> = {
  planning: { roads: true, buildings: true, terrain: true, projectModel: false, excavation: false },
  analysis: { roads: true, buildings: true, terrain: true, projectModel: true, excavation: true },
  presentation: { roads: false, buildings: true, terrain: true, projectModel: true, excavation: false },
};

const LAYER_TO_3D: Partial<Record<keyof LayerVisibility, Scene3DLayerKey>> = {
  terrain: "terrain",
  buildings: "buildings",
  roads: "roads",
  excavation: "excavation",
  projectModel: "flyover",
  utilities: "pipeline",
};

const SCENE3D_TO_LAYER: Partial<Record<Scene3DLayerKey, keyof LayerVisibility>> = {
  terrain: "terrain",
  buildings: "buildings",
  roads: "roads",
  excavation: "excavation",
  flyover: "projectModel",
  pipeline: "utilities",
};

function layerPatchToScene3d(partial: Partial<LayerVisibility>): Partial<Scene3DLayerVisibility> {
  const patch: Partial<Scene3DLayerVisibility> = {};
  for (const [key, value] of Object.entries(partial) as [keyof LayerVisibility, boolean][]) {
    const sceneKey = LAYER_TO_3D[key];
    if (sceneKey && value !== undefined) patch[sceneKey] = value;
  }
  return patch;
}

function scene3dPatchToLayers(partial: Partial<Scene3DLayerVisibility>): Partial<LayerVisibility> {
  const patch: Partial<LayerVisibility> = {};
  for (const [key, value] of Object.entries(partial) as [Scene3DLayerKey, boolean][]) {
    const layerKey = SCENE3D_TO_LAYER[key];
    if (layerKey && value !== undefined) patch[layerKey] = value;
  }
  return patch;
}

interface ProjectState {
  project: Project | null;
  setProject: (p: Project | null) => void;
  activeTool: MapTool;
  setActiveTool: (t: MapTool) => void;
  activateTool: (t: MapTool, hint?: ToolHint) => void;
  toolHint: ToolHint;
  setToolHint: (h: ToolHint) => void;
  drawnBoundary: GeoJSONGeometry | null;
  drawnAlignment: GeoJSONGeometry | null;
  setDrawnBoundary: (g: GeoJSONGeometry | null) => void;
  setDrawnAlignment: (g: GeoJSONGeometry | null) => void;
  drawVertices: [number, number][];
  setDrawVertices: (v: [number, number][]) => void;
  pushDrawVertex: (v: [number, number]) => void;
  popDrawVertex: () => void;
  clearDrawVertices: () => void;
  pendingSave: PendingSave | null;
  setPendingSave: (p: PendingSave | null) => void;
  finishDrawing: (p: PendingSave) => void;
  editVertices: [number, number][];
  editSnapshot: [number, number][];
  setEditVertices: (v: [number, number][]) => void;
  initEditFromGeometry: (g: GeoJSONGeometry) => void;
  revertEditVertices: () => void;
  snapEnabled: boolean;
  toggleSnap: () => void;
  snapRadiusPx: number;
  setSnapRadiusPx: (n: number) => void;
  corridorWidthM: number;
  setCorridorWidthM: (n: number) => void;
  measureHistory: MeasureEntry[];
  pushMeasureHistory: (entry: Omit<MeasureEntry, "id" | "at">) => void;
  clearMeasureHistory: () => void;
  layers: LayerVisibility;
  toggleLayer: (key: keyof LayerVisibility) => void;
  setLayers: (partial: Partial<LayerVisibility>) => void;
  applyLayerPreset: (preset: LayerPreset) => void;
  measureUnit: MeasureUnit;
  toggleMeasureUnit: () => void;
  modelLayers: ModelLayerVisibility;
  toggleModelLayer: (key: keyof ModelLayerVisibility) => void;
  cesiumTool: "orbit" | "pan" | "zoom" | "section" | "exploded";
  setCesiumTool: (t: "orbit" | "pan" | "zoom" | "section" | "exploded") => void;
  activeJob: JobStatus | null;
  setActiveJob: (j: JobStatus | null) => void;
  siteSuggestions: SiteSuggestion[];
  setSiteSuggestions: (s: SiteSuggestion[]) => void;
  highlightedSuggestionId: string | null;
  setHighlightedSuggestionId: (id: string | null) => void;
  mapRef: MapControls | null;
  setMapControls: (c: MapControls | null) => void;
  mapReady: boolean;
  setMapReady: (ready: boolean) => void;
  mapCursor: MapCursorState | null;
  setMapCursor: (c: MapCursorState | null) => void;
  workspaceFullscreen: boolean;
  setWorkspaceFullscreen: (v: boolean) => void;
  scene3dLayers: Scene3DLayerVisibility;
  toggleScene3dLayer: (key: Scene3DLayerKey) => void;
  setScene3dLayers: (partial: Partial<Scene3DLayerVisibility>) => void;
  undergroundView: boolean;
  toggleUndergroundView: () => void;
  selectedObject3d: Scene3DObjectInfo | null;
  setSelectedObject3d: (o: Scene3DObjectInfo | null) => void;
  scene3dMeasureTool: Scene3DMeasureTool;
  setScene3dMeasureTool: (t: Scene3DMeasureTool) => void;
  scene3dMeasureReadout: string | null;
  setScene3dMeasureReadout: (s: string | null) => void;
  surveyModeEnabled: boolean;
  setSurveyModeEnabled: (v: boolean) => void;
  surveyAccuracyTier: AccuracyTier;
  setSurveyAccuracyTier: (t: AccuracyTier) => void;
  surveyLayers: SurveyLayerVisibility;
  toggleSurveyLayer: (key: keyof SurveyLayerVisibility) => void;
  engineeringLayerFeatures: GeoJSONFeature[];
  setEngineeringLayerFeatures: (f: GeoJSONFeature[]) => void;
  surveyGcpFeatures: GeoJSONFeature[];
  setSurveyGcpFeatures: (f: GeoJSONFeature[]) => void;
  designMeshCatalog: { layer: string; name: string }[];
  designMeshVisibility: Record<string, boolean>;
  syncDesignMeshFromSpec: (spec: GeometrySpec | null | undefined) => void;
  toggleDesignMeshLayer: (layerId: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  project: null,
  setProject: (project) => set((state) => state.project?.id === project?.id ? { project } : { project, drawnBoundary: null, drawnAlignment: null, pendingSave: null, activeTool: "select", drawVertices: [], scene3dMeasureTool: "none" }),
  activeTool: "select",
  setActiveTool: (activeTool) =>
    set((s) => ({
      activeTool,
      drawVertices: activeTool === s.activeTool ? s.drawVertices : [],
      toolHint: activeTool === s.activeTool ? s.toolHint : null,
    })),
  activateTool: (activeTool, hint) =>
    set((s) => {
      const projectType = s.project?.project_type ?? "flyover";
      const nextHint = hint ?? null;
      const corridorWidthM =
        activeTool === "draw-corridor"
          ? defaultCorridorWidth(projectType, nextHint)
          : s.corridorWidthM;
      return {
        activeTool,
        toolHint: nextHint,
        drawVertices: [],
        corridorWidthM,
      };
    }),
  toolHint: null,
  setToolHint: (toolHint) => set({ toolHint }),
  drawnBoundary: null,
  drawnAlignment: null,
  setDrawnBoundary: (drawnBoundary) => set({ drawnBoundary }),
  setDrawnAlignment: (drawnAlignment) => set({ drawnAlignment }),
  drawVertices: [],
  setDrawVertices: (drawVertices) => set({ drawVertices }),
  pushDrawVertex: (v) => set((s) => ({ drawVertices: [...s.drawVertices, v] })),
  popDrawVertex: () => set((s) => ({ drawVertices: s.drawVertices.slice(0, -1) })),
  clearDrawVertices: () => set({ drawVertices: [] }),
  pendingSave: null,
  setPendingSave: (pendingSave) => set({ pendingSave }),
  finishDrawing: (pendingSave) => set({ pendingSave, activeTool: "select", drawVertices: [], toolHint: null,
    ...(pendingSave.kind === "boundary" ? { drawnBoundary: pendingSave.geometry } : { drawnAlignment: pendingSave.geometry }) }),
  editVertices: [],
  editSnapshot: [],
  setEditVertices: (editVertices) => set({ editVertices }),
  initEditFromGeometry: (g) => {
    const verts = geometryToVertices(g);
    set({ editVertices: verts, editSnapshot: [...verts] });
  },
  revertEditVertices: () => set((s) => ({ editVertices: [...s.editSnapshot] })),
  snapEnabled: true,
  toggleSnap: () => set((s) => ({ snapEnabled: !s.snapEnabled })),
  snapRadiusPx: 12,
  setSnapRadiusPx: (snapRadiusPx) => set({ snapRadiusPx }),
  corridorWidthM: 30,
  setCorridorWidthM: (corridorWidthM) => set({ corridorWidthM }),
  measureHistory: [],
  pushMeasureHistory: (entry) =>
    set((s) => ({
      measureHistory: [
        { ...entry, id: `${Date.now()}`, at: Date.now() },
        ...s.measureHistory,
      ].slice(0, 5),
    })),
  clearMeasureHistory: () => set({ measureHistory: [] }),
  layers: {
    satellite: false,
    roads: true,
    buildings: true,
    terrain: true,
    tiles3d: true,
    projectModel: true,
    excavation: true,
    utilities: true,
  },
  toggleLayer: (key) =>
    set((s) => {
      const next = !s.layers[key];
      const layers = { ...s.layers, [key]: next };
      const scene3dPatch = layerPatchToScene3d({ [key]: next });
      return {
        layers,
        scene3dLayers: { ...s.scene3dLayers, ...scene3dPatch },
      };
    }),
  setLayers: (partial) =>
    set((s) => ({
      layers: { ...s.layers, ...partial },
      scene3dLayers: { ...s.scene3dLayers, ...layerPatchToScene3d(partial) },
    })),
  applyLayerPreset: (preset) =>
    set((s) => {
      const partial = LAYER_PRESETS[preset];
      return {
        layers: { ...s.layers, ...partial },
        scene3dLayers: { ...s.scene3dLayers, ...layerPatchToScene3d(partial) },
      };
    }),
  measureUnit: "m",
  toggleMeasureUnit: () =>
    set((s) => ({ measureUnit: s.measureUnit === "m" ? "ft" : "m" })),
  modelLayers: {
    outer: true,
    inner: false,
    foundation: true,
    steel: false,
    concrete: true,
    drainage: true,
    electrical: false,
    pipeline: true,
    traffic: false,
  },
  toggleModelLayer: (key) =>
    set((s) => ({ modelLayers: { ...s.modelLayers, [key]: !s.modelLayers[key] } })),
  cesiumTool: "orbit",
  setCesiumTool: (cesiumTool) => set({ cesiumTool }),
  activeJob: null,
  setActiveJob: (activeJob) => set({ activeJob }),
  siteSuggestions: [],
  setSiteSuggestions: (siteSuggestions) => set({ siteSuggestions }),
  highlightedSuggestionId: null,
  setHighlightedSuggestionId: (highlightedSuggestionId) => set({ highlightedSuggestionId }),
  mapRef: null,
  setMapControls: (mapRef) => set({ mapRef }),
  mapReady: false,
  setMapReady: (mapReady) => set({ mapReady }),
  mapCursor: null,
  setMapCursor: (mapCursor) => set({ mapCursor }),
  workspaceFullscreen: false,
  setWorkspaceFullscreen: (workspaceFullscreen) => set({ workspaceFullscreen }),
  scene3dLayers: defaultScene3DLayers(),
  toggleScene3dLayer: (key) =>
    set((s) => {
      const next = !s.scene3dLayers[key];
      const scene3dLayers = { ...s.scene3dLayers, [key]: next };
      const layerPatch = scene3dPatchToLayers({ [key]: next });
      return {
        scene3dLayers,
        layers: { ...s.layers, ...layerPatch },
      };
    }),
  setScene3dLayers: (partial) =>
    set((s) => ({
      scene3dLayers: { ...s.scene3dLayers, ...partial },
      layers: { ...s.layers, ...scene3dPatchToLayers(partial) },
    })),
  undergroundView: false,
  toggleUndergroundView: () => set((s) => ({ undergroundView: !s.undergroundView })),
  selectedObject3d: null,
  setSelectedObject3d: (selectedObject3d) => set({ selectedObject3d }),
  scene3dMeasureTool: "none",
  setScene3dMeasureTool: (scene3dMeasureTool) => set({ scene3dMeasureTool }),
  scene3dMeasureReadout: null,
  setScene3dMeasureReadout: (scene3dMeasureReadout) => set({ scene3dMeasureReadout }),
  surveyModeEnabled: false,
  setSurveyModeEnabled: (surveyModeEnabled) => set({ surveyModeEnabled }),
  surveyAccuracyTier: "visual",
  setSurveyAccuracyTier: (surveyAccuracyTier) => set({ surveyAccuracyTier }),
  surveyLayers: {
    visualBasemap: true,
    surveyOrtho: true,
    surveyDem: true,
    surveyVectors: true,
    surveyGcp: true,
  },
  toggleSurveyLayer: (key) =>
    set((s) => ({ surveyLayers: { ...s.surveyLayers, [key]: !s.surveyLayers[key] } })),
  engineeringLayerFeatures: [],
  setEngineeringLayerFeatures: (engineeringLayerFeatures) => set({ engineeringLayerFeatures }),
  surveyGcpFeatures: [],
  setSurveyGcpFeatures: (surveyGcpFeatures) => set({ surveyGcpFeatures }),
  designMeshCatalog: [],
  designMeshVisibility: {},
  syncDesignMeshFromSpec: (spec) =>
    set((s) => {
      if (!spec?.objects?.length) {
        return { designMeshCatalog: [], designMeshVisibility: {} };
      }
      const groups = extractDesignMeshLayers(spec);
      const catalog = spec.objects.map((o) => ({
        layer: o.layer || "misc",
        name: o.name,
      }));
      const visibility: Record<string, boolean> = {};
      for (const group of groups) {
        visibility[group.id] = s.designMeshVisibility[group.id] ?? true;
      }
      return { designMeshCatalog: catalog, designMeshVisibility: visibility };
    }),
  toggleDesignMeshLayer: (layerId) =>
    set((s) => ({
      designMeshVisibility: {
        ...s.designMeshVisibility,
        [layerId]: !s.designMeshVisibility[layerId],
      },
    })),
}));
