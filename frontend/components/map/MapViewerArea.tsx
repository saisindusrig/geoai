"use client";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import WorkspaceSearch from "@/components/map/WorkspaceSearch";
import { useWorkspacePanel } from "@/hooks/useWorkspacePanel";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Compass, Crosshair, Globe, LocateFixed, PanelLeft, Bot, ScanEye, SlidersHorizontal } from "lucide-react";
import SiteSuggestionsPanel from "@/components/map/SiteSuggestionsPanel";
import MapToolbarExtended from "@/components/map/MapToolbarExtended";
import Scene3DOverlay from "@/components/map/Scene3DOverlay";
import ElevationProfileChart from "@/components/map/ElevationProfileChart";
import CommandPalette from "@/components/layout/CommandPalette";
import { useWorkspaceMap } from "@/components/layout/WorkspaceMapContext";
import { Button } from "@/components/ui/button";
import MapToolbarToggle from "@/components/ui/map-toolbar-toggle";
import { Input } from "@/components/ui/input";
import { api, formatApiErrorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";
import type { EditableModelDocument, GeoJSONFeature, GeoJSONGeometry, GeocodeResult, Project, SiteAnalysis } from "@/lib/types";
import type { SiteSuggestion } from "@/lib/site-suggestions";
import { generateSiteSuggestions } from "@/lib/site-suggestions";
import { useProjectStore } from "@/stores/projectStore";
import { basemapFor3d, type MapBasemap } from "@/lib/map-imagery";
import MapStyleToggle from "@/components/ui/map-style-toggle";
import { cn } from "@/lib/utils";

const CesiumView = dynamic(() => import("@/components/map/CesiumView"), { ssr: false });

interface Props {
  project: Project;
  modelUrl?: string | null;
  excavationUrl?: string | null;
  onBoundaryDrawn?: (g: GeoJSONGeometry) => void;
  onAlignmentDrawn?: (g: GeoJSONGeometry) => void;
  onLocationChange?: (lng: number, lat: number, name: string) => void | Promise<void>;
  onGenerate?: () => void;
  onAnalyze?: () => void;
  defaultView?: "2d" | "3d";
  showToolbar?: boolean;
  showSuggestionsPanel?: boolean;
  editor?: EditableModelEditor;
  editableModel?: EditableModelDocument | null;
  modelRevisionId?: number;
  selectedComponentIds?: string[];
  onSelectComponent?: (id: string | null, additive?: boolean) => void;
}

export default function MapViewerArea({
  project,
  modelUrl,
  excavationUrl,
  onBoundaryDrawn,
  onAlignmentDrawn,
  onLocationChange,
  onGenerate,
  onAnalyze,
  showToolbar = true,
  showSuggestionsPanel = true,
  editor,
  editableModel,
  modelRevisionId,
  selectedComponentIds = [],
  onSelectComponent,
}: Props) {
  const projectLng = project.center_lng ?? 77.5946;
  const projectLat = project.center_lat ?? 12.9716;
  const projectLocationKey = `${project.id}:${projectLng}:${projectLat}:${project.location_name ?? ""}`;

  const view: "2d" | "3d" = "3d";
  const pendingGeometry = useProjectStore(state => state.pendingSave);
  const drawnBoundary = useProjectStore(state => state.drawnBoundary);
  const drawnAlignment = useProjectStore(state => state.drawnAlignment);
  const [basemap, setBasemap] = useState<MapBasemap>("satellite");
  const [searchDraft, setSearchDraft] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<GeocodeResult[]>([]);
  const [mapCenterOverride, setMapCenterOverride] = useState<[number, number] | null>(null);
  const [locationSyncKey, setLocationSyncKey] = useState(projectLocationKey);
  const [analysis, setAnalysis] = useState<SiteAnalysis | null>(null);
  const [satelliteBrightness, setSatelliteBrightness] = useState(100);
  const [overlayOpacity, setOverlayOpacity] = useState(85);
  const [terrainExaggeration, setTerrainExaggeration] = useState(1);
  const { open: locationSearchOpen, close: closeLocationSearch, toggle: toggleLocationSearch } = useWorkspacePanel("search");
  const {
    setSiteSuggestions,
    layers,
    surveyModeEnabled,
    engineeringLayerFeatures,
    surveyGcpFeatures,
    surveyLayers,
    undergroundView,
    toggleUndergroundView,
    mapRef,
    mapCursor,
  } = useProjectStore();
  const { focusMode, toolsOpen, copilotOpen, onOpenTools, onOpenCopilot } = useWorkspaceMap();

  if (projectLocationKey !== locationSyncKey) {
    setLocationSyncKey(projectLocationKey);
    setMapCenterOverride(null);
    setSearchDraft(null);
  }

  useEffect(() => {

    if (basemap === "terrain") {
      queueMicrotask(() => setBasemap("satellite"));
      useProjectStore.getState().setLayers({ satellite: true });
    }
    useProjectStore.getState().setLayers({ terrain: true });
  }, [basemap]);

  const activeBasemap: MapBasemap =
    layers.satellite && basemap === "satellite" ? "satellite" : basemap;

  const mapCenter: [number, number] = useMemo(
    () => mapCenterOverride ?? [projectLng, projectLat],
    [mapCenterOverride, projectLng, projectLat],
  );
  const search = searchDraft ?? project.location_name ?? "";

  useEffect(() => {
    if (project.status === "local") {
      queueMicrotask(() => setAnalysis(null));
      return;
    }
    let cancelled = false;
    api
      .getOptional<SiteAnalysis>(`/api/projects/${project.id}/site-analysis`)
      .then((data) => {
        if (!cancelled) setAnalysis(data);
      });
    return () => {
      cancelled = true;
    };
  }, [project.id, project.status]);

  const roadFeatures = useMemo(
    () => (analysis?.nearby_roads_json?.features ?? []) as GeoJSONFeature[],
    [analysis],
  );

  const buildingFeatures = useMemo(
    () => (analysis?.existing_buildings_json?.features ?? []) as GeoJSONFeature[],
    [analysis],
  );

  const waterFeatures = useMemo(() => {
    const raw = analysis?.raw_geojson?.features ?? [];
    return raw.filter(
      (f) => f.properties?.category === "waterway" || f.properties?.natural === "water",
    ) as GeoJSONFeature[];
  }, [analysis]);

  useEffect(() => {
    const onSaveProject = async () => {
      const { pendingSave, drawnBoundary, drawnAlignment } = useProjectStore.getState();
      const boundaryDraft = drawnBoundary ?? (pendingSave?.kind === "boundary" ? pendingSave.geometry : null);
      const alignmentDraft = drawnAlignment ?? (pendingSave?.kind === "alignment" ? pendingSave.geometry : null);
      try {
        if (boundaryDraft || alignmentDraft) {
          const body = {
            ...(boundaryDraft ? { boundary_geojson: boundaryDraft } : {}),
            ...(alignmentDraft ? { alignment_geojson: alignmentDraft } : {}),
          };
          await api.put(`/api/projects/${project.id}`, body);
          if (boundaryDraft) await onBoundaryDrawn?.(boundaryDraft);
          if (alignmentDraft) await onAlignmentDrawn?.(alignmentDraft);
          useProjectStore.setState(state => ({
            pendingSave: state.pendingSave === pendingSave ? null : state.pendingSave,
            drawnBoundary: state.drawnBoundary === drawnBoundary ? null : state.drawnBoundary,
            drawnAlignment: state.drawnAlignment === drawnAlignment ? null : state.drawnAlignment,
          }));
          toast("Project geometry saved", { variant: "success" });
          return;
        }
        const body: Record<string, unknown> = {};
        if (project.boundary_geojson) body.boundary_geojson = project.boundary_geojson;
        if (project.alignment_geojson) body.alignment_geojson = project.alignment_geojson;
        if (project.center_lat != null && project.center_lng != null) {
          body.center_lat = project.center_lat;
          body.center_lng = project.center_lng;
          if (project.location_name) body.location_name = project.location_name;
        }
        if (!Object.keys(body).length) {
          toast("Nothing to save", { variant: "default", description: "Draw a boundary or alignment first." });
          return;
        }
        await api.put(`/api/projects/${project.id}`, body);
        toast("Project saved", { variant: "success" });
      } catch (e) {
        toast("Save failed", { variant: "error", description: formatApiErrorMessage(e) });
      }
    };
    window.addEventListener("geoai:save-project", onSaveProject);
    return () => window.removeEventListener("geoai:save-project", onSaveProject);
  }, [project, onBoundaryDrawn, onAlignmentDrawn]);

  useEffect(() => {
    if (!project.boundary_geojson && project.center_lng != null && project.center_lat != null) {
      api
        .post<{ suggestions: SiteSuggestion[] }>(`/api/projects/${project.id}/site-suggestions`, {
          lng: project.center_lng,
          lat: project.center_lat,
        })
        .then((res) => setSiteSuggestions(res.suggestions.slice(0, 6)))
        .catch(() => {
          const list = generateSiteSuggestions(
            project.center_lng!,
            project.center_lat!,
            project.project_type,
            roadFeatures,
          );
          setSiteSuggestions(list.slice(0, 6));
        });
    }
  }, [
    project.boundary_geojson,
    project.center_lng,
    project.center_lat,
    project.project_type,
    project.id,
    roadFeatures,
    setSiteSuggestions,
  ]);

  const doSearch = async () => {
    if (search.length < 2) return;
    setSearching(true);
    setResults([]);
    try {
      const data = await api.get<{ results: GeocodeResult[] }>(
        `/api/geocode?q=${encodeURIComponent(search)}`,
      );
      setResults(data.results);
      if (data.results.length === 1) pickResult(data.results[0]);
    } finally {
      setSearching(false);
    }
  };

  const pickResult = async (r: GeocodeResult) => {
    setSearchDraft(r.name);
    setResults([]);
    setMapCenterOverride([r.lng, r.lat]);
    await onLocationChange?.(r.lng, r.lat, r.name);
  };

  const handleBasemap = (mode: typeof basemap) => {
    if (view === "3d" && mode === "terrain") return;
    setBasemap(mode);
    useProjectStore.getState().setLayers({ satellite: mode === "satellite" });
  };

  useEffect(() => {
    const onLocationSearch = () => toggleLocationSearch();
    window.addEventListener("geoai:open-location-search", onLocationSearch);
    return () => { window.removeEventListener("geoai:open-location-search", onLocationSearch); };
  }, [toggleLocationSearch]);

  const handleUseMapCenter = async () => {
    const viewport = mapRef?.getViewport?.();
    const center = viewport?.center ?? mapCenter;
    const name = `Map center ${center[1].toFixed(5)}, ${center[0].toFixed(5)}`;
    setSearchDraft(name);
    setMapCenterOverride(center);
    await onLocationChange?.(center[0], center[1], name);
  };

  const recenterHome = () => {
    if (mapRef?.flyHome) {
      mapRef.flyHome();
      return;
    }
    setMapCenterOverride([projectLng, projectLat]);
  };

  const applyBoundary = useCallback(
    async (s: SiteSuggestion) => {
      await onBoundaryDrawn?.(s.geometry);
    },
    [onBoundaryDrawn],
  );

  const applyAlignment = useCallback(
    async (s: SiteSuggestion) => {
      await onAlignmentDrawn?.(s.geometry);
    },
    [onAlignmentDrawn],
  );

  return (
    <div
      className={cn(
        "absolute inset-0 overflow-hidden map-viewport",
      )}
    >
      <CommandPalette projectId={project.id} onAnalyze={onAnalyze} onGenerate={onGenerate} />

      {showToolbar && (
        <div
          className={cn(
            "absolute z-20 top-3 flex flex-col gap-2 pointer-events-none",
            focusMode ? "left-14 right-3" : "left-3 right-3",
          )}
        >
          <div className="flex items-start gap-2">
            <div className="relative pointer-events-auto flex min-h-11 min-w-0 max-w-md flex-1 items-center gap-1 rounded-2xl border border-border bg-[rgba(5,7,10,0.72)] px-2 py-1.5 shadow-[0_18px_44px_rgba(0,0,0,0.34)] backdrop-blur-xl sm:max-w-lg">
              <LocateFixed className="h-4 w-4 shrink-0 text-accent" />
              <Input
                value={search}
                onChange={(e) => setSearchDraft(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && doSearch()}
                placeholder="Search location…"
                className="h-8 min-w-0 flex-1 border-0 bg-transparent text-xs text-foreground focus:ring-0"
              />
              <button
                type="button"
                onClick={() => void handleUseMapCenter()}
                className="hidden h-8 shrink-0 items-center gap-1 rounded-lg border border-border bg-white/[0.04] px-2 text-[10px] text-foreground-secondary hover:bg-surface-hover hover:text-foreground sm:flex"
                title="Use current map center"
              >
                <Crosshair className="h-3.5 w-3.5" />
                Center
              </button>
              <Button size="sm" className="h-8 shrink-0 px-2" onClick={doSearch} disabled={searching}>
                <Globe className="h-3.5 w-3.5" />
              </Button>
              {results.length > 0 && (
                <ul className="absolute left-0 right-0 top-full z-30 mt-2 max-h-52 overflow-hidden overflow-y-auto rounded-xl border border-border bg-[rgba(11,17,28,0.98)] shadow-2xl backdrop-blur-xl">
                  <li>
                    <button
                      type="button"
                      onClick={() => void handleUseMapCenter()}
                      className="flex w-full items-center gap-2 border-b border-border px-3 py-2 text-left text-xs text-foreground-secondary hover:bg-primary/10"
                    >
                      <Crosshair className="h-3.5 w-3.5 text-accent" />
                      Use map center
                    </button>
                  </li>
                  {results.map((r, i) => (
                    <li key={i}>
                      <button
                        type="button"
                        onClick={() => pickResult(r)}
                        className="w-full border-b border-border px-3 py-2 text-left text-xs text-foreground-secondary last:border-0 hover:bg-primary/10"
                      >
                        {r.name}
                        <span className="ml-1 text-muted-foreground">({r.provider})</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="pointer-events-auto shrink-0">
              <MapStyleToggle
                value={view === "3d" ? basemapFor3d(activeBasemap) : activeBasemap}
                onChange={handleBasemap}
                view={view}
                compact
              />
            </div>

            {view === "3d" && (
              <div className="pointer-events-auto flex shrink-0 items-center gap-1">
                <MapToolbarToggle
                  label="Transparent"
                  icon={ScanEye}
                  active={undergroundView}
                  onChange={() => toggleUndergroundView()}
                  title={
                    undergroundView
                      ? "Turn off transparent ground (opaque terrain)"
                      : "Turn on transparent ground (see underground)"
                  }
                />
              </div>
            )}

            <div className="pointer-events-auto panel-glass flex shrink-0 items-center gap-0.5 rounded-md px-1 py-1">
              <MapToolbarExtended view={view} />
            </div>

            <div className="pointer-events-auto hidden shrink-0 items-center gap-1 rounded-2xl border border-border bg-[rgba(5,7,10,0.68)] p-1 shadow-lg backdrop-blur-xl md:flex">
              <button
                type="button"
                onClick={recenterHome}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-foreground-secondary hover:bg-surface-hover hover:text-foreground"
                title="Home / reset view"
              >
                <LocateFixed className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => mapRef?.resetNorth?.()}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-foreground-secondary hover:bg-surface-hover hover:text-foreground"
                title="Reset north"
              >
                <Compass className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="pointer-events-auto hidden max-w-3xl items-center gap-2 overflow-x-auto rounded-2xl border border-[rgba(148,163,184,0.14)] bg-[rgba(5,7,10,0.62)] px-2 py-1.5 text-[10px] text-muted-foreground shadow-lg backdrop-blur-xl lg:flex">
            <div className="flex shrink-0 items-center gap-1.5 text-foreground-secondary">
              <SlidersHorizontal className="h-3.5 w-3.5 text-accent" />
              Map tuning
            </div>
            {[
              ["Satellite brightness", satelliteBrightness, setSatelliteBrightness, 60, 120, "%"],
              ["Overlay opacity", overlayOpacity, setOverlayOpacity, 20, 100, "%"],
              ["Terrain exaggeration", terrainExaggeration, setTerrainExaggeration, 1, 3, "x"],
            ].map(([label, value, setter, min, max, suffix]) => (
              <label key={label as string} className="flex shrink-0 items-center gap-1.5">
                <span>{label as string}</span>
                <input
                  type="range"
                  min={min as number}
                  max={max as number}
                  step={label === "Terrain exaggeration" ? 0.5 : 1}
                  value={value as number}
                  onChange={(e) => (setter as (value: number) => void)(Number(e.target.value))}
                  className="h-1 w-20 accent-primary"
                />
                <span className="w-8 font-data text-foreground-secondary">
                  {value as number}{suffix as string}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {!showToolbar && locationSearchOpen && (
        <WorkspaceSearch onClose={closeLocationSearch} onNavigate={(lng, lat) => setMapCenterOverride([lng, lat])} />
      )}

      {showSuggestionsPanel && false && (
        <div className="absolute top-16 right-3 z-20 w-[220px] max-h-[calc(100%-6rem)] overflow-y-auto pointer-events-auto panel-glass rounded-lg p-2 hidden lg:block">
          <SiteSuggestionsPanel
            compact
            projectId={project.id}
            projectType={project.project_type}
            centerLng={mapCenter[0]}
            centerLat={mapCenter[1]}
            roadFeatures={roadFeatures}
            buildingFeatures={buildingFeatures}
            onApplyBoundary={applyBoundary}
            onApplyAlignment={applyAlignment}
          />
        </div>
      )}

      {focusMode && !toolsOpen && (
        <div className="absolute bottom-20 left-3 z-20 pointer-events-auto">
          <Button
            variant="default"
            size="sm"
            className="h-auto min-w-[2.75rem] flex-col gap-0.5 py-2 px-1.5 panel-glass border-primary/30 shadow-md"
            title="Engineering Tools"
            onClick={onOpenTools}
            aria-label="Open Engineering Tools"
          >
            <PanelLeft className="h-4 w-4" />
            <span className="text-[8px] font-semibold leading-none">Tools</span>
          </Button>
        </div>
      )}

      {focusMode && !copilotOpen && (
        <div className="absolute bottom-20 right-3 z-20 pointer-events-auto">
          <Button
            size="sm"
            className="h-auto min-w-[2.75rem] flex-col gap-0.5 py-2 px-1.5 panel-glass border-primary/30 shadow-md"
            title="AI Copilot"
            onClick={onOpenCopilot}
            aria-label="Open AI Copilot"
          >
            <Bot className="h-4 w-4 text-primary" />
            <span className="text-[8px] font-semibold leading-none">Copilot</span>
          </Button>
        </div>
      )}

      {false && <ElevationProfileChart project={project} />}
      {view === "3d" && <Scene3DOverlay />}

      <div className="pointer-events-none absolute bottom-9 left-1/2 z-20 flex -translate-x-1/2 items-center gap-2 rounded-full border border-white/15 bg-background/85 px-3 py-1.5 text-[10px] text-muted-foreground shadow-lg backdrop-blur-xl">
        <LocateFixed className="size-3 text-primary" />
        <span className="font-data">{(mapCursor?.lngLat?.[1] ?? mapCenter[1]).toFixed(5)}° N · {(mapCursor?.lngLat?.[0] ?? mapCenter[0]).toFixed(5)}° E</span>
      </div>

      <div
        className="absolute inset-0"
        style={{
          filter: `brightness(${satelliteBrightness}%)`,
        }}
      >
        {(
          <CesiumView
            key={project.id}
            projectId={project.id}
            center={mapCenter}
            terrainExaggeration={terrainExaggeration}
            basemap={basemapFor3d(activeBasemap)}
            boundary={pendingGeometry?.kind === "boundary" ? pendingGeometry.geometry : drawnBoundary ?? project.boundary_geojson}
            alignment={pendingGeometry?.kind === "alignment" ? pendingGeometry.geometry : drawnAlignment ?? project.alignment_geojson}
            modelUrl={modelUrl ?? null}
            excavationUrl={excavationUrl ?? null}
            useModelLayers={false}
            roadFeatures={surveyModeEnabled && surveyLayers.surveyVectors ? engineeringLayerFeatures : roadFeatures}
            buildingFeatures={buildingFeatures}
            waterFeatures={waterFeatures}
            surveyMode={surveyModeEnabled}
            surveyGcpFeatures={surveyGcpFeatures}
            disableVendor3DTiles={surveyModeEnabled && !surveyLayers.visualBasemap}
            editor={editor}
            editableModel={editableModel}
            modelRevisionId={modelRevisionId}
            selectedComponentIds={selectedComponentIds}
            onSelectComponent={onSelectComponent}
          />
        )}
      </div>

      {view === "3d" && !modelUrl && !excavationUrl && !editableModel && !drawnAlignment && !project.alignment_geojson && (
        <div className="pointer-events-none absolute inset-x-4 bottom-24 z-10 flex justify-center">
          <div className="max-w-md rounded-2xl border border-border bg-[rgba(5,7,10,0.72)] px-4 py-3 text-center shadow-lg backdrop-blur-xl">
            <p className="text-sm font-semibold text-foreground">Draw an alignment or generate a concept</p>
            <p className="mt-1 text-[12px] leading-snug text-muted-foreground">
              AI model layers appear here after design generation completes.
            </p>
          </div>
        </div>
      )}


    </div>
  );
}







