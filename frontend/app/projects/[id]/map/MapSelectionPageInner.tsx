"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import BottomSummaryBar from "@/components/layout/BottomSummaryBar";
import DrawingToolsPanel from "@/components/layout/DrawingToolsPanel";
import DrawingToolsToolbar from "@/components/layout/DrawingToolsToolbar";
import ProjectValidationPanel from "@/components/project/ProjectValidationPanel";
import SiteSuggestionsPanel from "@/components/map/SiteSuggestionsPanel";
import { ProjectError, ProjectLoading } from "@/components/layout/ProjectHeader";
import WorkspaceLayout from "@/components/layout/WorkspaceLayout";
import WorkspaceLeftSidebar from "@/components/layout/WorkspaceLeftSidebar";
import MapViewerArea from "@/components/map/MapViewerArea";
import { useProjectData } from "@/hooks/useProjectData";
import { api } from "@/lib/api";
import { toastPromise } from "@/lib/toast";
import type { GeoJSONGeometry } from "@/lib/types";
import { type MapTool, useProjectStore } from "@/stores/projectStore";
import { cn } from "@/lib/utils";

export default function MapSelectionPageInner() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = Number(params.id);
  const { project, design, summaryStats, loading, error, load, modelFile, excavationFile } =
    useProjectData(projectId);
  const { setActiveTool } = useProjectStore();
  const workspaceFullscreen = useProjectStore((s) => s.workspaceFullscreen);

  useEffect(() => {
    const tool = searchParams.get("tool") as MapTool | null;
    if (tool) setActiveTool(tool);
  }, [searchParams, setActiveTool]);

  const saveBoundary = async (g: GeoJSONGeometry) => {
    await toastPromise(api.put(`/api/projects/${projectId}`, { boundary_geojson: g }), {
      loading: "Saving boundary…",
      success: "Boundary saved",
    });
    load();
  };

  const saveAlignment = async (g: GeoJSONGeometry) => {
    await toastPromise(api.put(`/api/projects/${projectId}`, { alignment_geojson: g }), {
      loading: "Saving alignment…",
      success: "Alignment saved",
    });
    load();
  };

  const saveLocation = async (lng: number, lat: number, name: string) => {
    await toastPromise(
      api.put(`/api/projects/${projectId}`, {
        center_lng: lng,
        center_lat: lat,
        location_name: name,
      }),
      { loading: "Updating location…", success: "Location updated" },
    );
    load();
  };

  if (loading) return <ProjectLoading message="Loading map…" />;
  if (error || !project) return <ProjectError error={error || "Not found"} onRetry={load} />;

  const drawingToolProps = {
    projectId,
    projectType: project.project_type,
    boundary: project.boundary_geojson,
    alignment: project.alignment_geojson,
    onImportBoundary: async (g: GeoJSONGeometry) => saveBoundary(g),
    onImportAlignment: async (g: GeoJSONGeometry) => saveAlignment(g),
    onSaveBoundary: saveBoundary,
    onSaveAlignment: saveAlignment,
  };

  const leftPanel = (
    <WorkspaceLeftSidebar
      tools={
        <DrawingToolsPanel hidePrimaryTools {...drawingToolProps} />
      }
      middle={
        <div className="space-y-3">
          <ProjectValidationPanel projectId={projectId} compact />
          <SiteSuggestionsPanel
          sidebar
          projectId={projectId}
          projectType={project.project_type}
          centerLng={project.center_lng ?? 77.5946}
          centerLat={project.center_lat ?? 12.9716}
          onApplyBoundary={async (s) => saveBoundary(s.geometry)}
          onApplyAlignment={async (s) => saveAlignment(s.geometry)}
        />
        </div>
      }
    />
  );

  return (
    <div className={cn("flex flex-1 flex-col min-h-0 overflow-hidden", !workspaceFullscreen && "pb-14 md:pb-0")}>
      <WorkspaceLayout
        projectId={projectId}
        toolbar={
          <DrawingToolsToolbar
            projectType={project.project_type}
            boundary={project.boundary_geojson}
            alignment={project.alignment_geojson}
            onSaveBoundary={saveBoundary}
            onSaveAlignment={saveAlignment}
          />
        }
        ai={{
          projectId,
          design,
          onApplyParameters: () => router.push(`/projects/${projectId}/workspace#copilot`),
          onRegenerate: () => router.push(`/projects/${projectId}/workspace#copilot`),
        }}
        leftPanel={leftPanel}
        map={
          <MapViewerArea
            project={project}
            modelUrl={modelFile?.file_url}
            excavationUrl={excavationFile?.file_url}
            onBoundaryDrawn={saveBoundary}
            onAlignmentDrawn={saveAlignment}
            onLocationChange={saveLocation}
            onAnalyze={() => router.push(`/projects/${projectId}/analysis`)}
            onGenerate={() => router.push(`/projects/${projectId}/workspace`)}
            showSuggestionsPanel={false}
          />
        }
      />

      {!workspaceFullscreen && (
        <>
          <BottomSummaryBar stats={summaryStats} />
        </>
      )}
    </div>
  );
}
