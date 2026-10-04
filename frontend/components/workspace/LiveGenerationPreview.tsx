"use client";

import { MapboxOverlay } from "@deck.gl/mapbox";
import type maplibregl from "maplibre-gl";
import { Eye, EyeOff, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { buildPreviewLayout } from "@/lib/map/generation-preview-geometry";
import { buildGenerationPreviewLayers } from "@/lib/map/generation-preview-layers";
import type { JobStage } from "@/lib/generation-job";
import { stageLabel, stageMapLabel } from "@/lib/generation-job";
import type { Project } from "@/lib/types";
import { useProjectStore } from "@/stores/projectStore";

const PREVIEW_KEY = "geoai-live-generation-preview";

function readPreviewEnabled() {
  if (typeof window === "undefined") return true;
  return localStorage.getItem(PREVIEW_KEY) !== "false";
}

function mapJobStageToPreview(stage?: JobStage | null): JobStage | "idle" {
  if (!stage || stage === "completed" || stage === "failed") return "idle";
  return stage;
}

interface LiveGenerationPreviewProps {
  map: maplibregl.Map | null;
  project: Project;
  onCancel?: () => void;
  cancelling?: boolean;
}

export default function LiveGenerationPreview({
  map,
  project,
  onCancel,
  cancelling,
}: LiveGenerationPreviewProps) {
  const activeJob = useProjectStore((s) => s.activeJob);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const [enabled, setEnabled] = useState(readPreviewEnabled);
  const [pulse, setPulse] = useState(0);
  const [scanProgress, setScanProgress] = useState(0);

  const layout = useMemo(
    () =>
      buildPreviewLayout({
        boundary: project.boundary_geojson,
        alignment: project.alignment_geojson,
        center: [project.center_lng ?? 77.5946, project.center_lat ?? 12.9716],
        projectType: project.project_type,
        projectId: project.id,
      }),
    [
      project.alignment_geojson,
      project.boundary_geojson,
      project.center_lat,
      project.center_lng,
      project.id,
      project.project_type,
    ],
  );

  const stage = mapJobStageToPreview(activeJob?.stage);
  const visibleCount = useMemo(() => {
    if (!activeJob?.stage) return 1;
    const stageIndex: Record<string, number> = {
      queued: 1,
      analyzing_site: 2,
      generating_layout: 3,
      generating_3d_preview: 4,
      calculating_boq: 5,
      exporting_model: 6,
      saving_result: 6,
    };
    return stageIndex[activeJob.stage] ?? 1;
  }, [activeJob?.stage]);
  const useGhostPreview = enabled && !activeJob?.preview_ready;
  const active =
    enabled &&
    activeJob &&
    activeJob.status !== "completed" &&
    activeJob.status !== "failed" &&
    stage !== "idle";

  useEffect(() => {
    if (!active) return;
    let raf = 0;
    const tick = () => {
      const now = Date.now();
      setPulse((now % 2000) / 2000);
      setScanProgress((now % 4000) / 4000);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active]);

  const layers = useMemo(() => {
    if (!active || !map || !useGhostPreview) return [];
    return buildGenerationPreviewLayers({
      layout,
      stage,
      pulse,
      scanProgress,
      visibleCount,
      showLabels: stage === "calculating_boq" || stage === "exporting_model" || stage === "saving_result",
    });
  }, [active, layout, map, pulse, scanProgress, stage, useGhostPreview, visibleCount]);

  useEffect(() => {
    if (!map || !enabled) {
      overlayRef.current?.setProps({ layers: [] });
      return;
    }
    if (!overlayRef.current) {
      overlayRef.current = new MapboxOverlay({ interleaved: false, layers: [] });
      map.addControl(overlayRef.current as unknown as maplibregl.IControl);
    }
    overlayRef.current.setProps({ layers });
  }, [enabled, layers, map]);

  useEffect(
    () => () => {
      if (overlayRef.current && map) {
        try {
          map.removeControl(overlayRef.current as unknown as maplibregl.IControl);
        } catch {
          // map disposed
        }
      }
      overlayRef.current = null;
    },
    [map],
  );

  const toggleEnabled = useCallback(() => {
    setEnabled((value) => {
      const next = !value;
      localStorage.setItem(PREVIEW_KEY, String(next));
      return next;
    });
  }, []);

  if (!activeJob || activeJob.status === "completed" || activeJob.status === "failed") {
    return null;
  }

  const chipLabel = activeJob.stage_label ?? stageLabel(stage);
  const mapStatus =
    activeJob.message ??
    (activeJob.preview_ready ? "Preview ready — final model generating" : stageMapLabel(stage));

  return (
    <div className="pointer-events-none absolute left-1/2 top-20 z-[85] -translate-x-1/2">
      <div className="pointer-events-auto panel-glass flex flex-wrap items-center gap-2 rounded-lg px-3 py-2 text-[11px] shadow-md max-w-[min(92vw,520px)]">
        <span className="font-medium text-foreground">{chipLabel}</span>
        {enabled && mapStatus && (
          <span className="text-muted-foreground">· {mapStatus}</span>
        )}
        {activeJob.progress != null && (
          <span className="font-data text-[10px] text-muted-foreground">{activeJob.progress}%</span>
        )}
        <button
          type="button"
          onClick={toggleEnabled}
          className="flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-surface-hover hover:text-foreground"
        >
          {enabled ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
          Preview
        </button>
        {onCancel && activeJob.status !== "cancelled" && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={cancelling}
            onClick={onCancel}
            className="h-6 gap-1 px-2 text-[10px] text-destructive hover:bg-destructive-muted"
          >
            <XCircle className="h-3 w-3" />
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
}
