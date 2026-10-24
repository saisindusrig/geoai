"use client";

import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import {
  Box,
  Eye,
  Layers,
  Maximize2,
  Minimize2,
  Move3d,
  Rotate3d,
  Scissors,
  SlidersHorizontal,
  ZoomIn,
} from "lucide-react";
import BottomSummaryBar from "@/components/layout/BottomSummaryBar";
import { ProjectError, ProjectLoading } from "@/components/layout/ProjectHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useProjectData } from "@/hooks/useProjectData";
import { MODEL_LAYER_DEFS, MODEL_LAYER_GROUPS } from "@/lib/model-layers";
import { cn } from "@/lib/utils";
import { type ModelLayerVisibility, useProjectStore } from "@/stores/projectStore";

const CesiumView = dynamic(() => import("@/components/map/CesiumView"), { ssr: false });

const VIEW_TOOLS: {
  icon: typeof Rotate3d;
  label: string;
  tool: "orbit" | "pan" | "zoom" | "exploded" | "section";
}[] = [
  { icon: Rotate3d, label: "Orbit", tool: "orbit" },
  { icon: Move3d, label: "Pan", tool: "pan" },
  { icon: ZoomIn, label: "Zoom", tool: "zoom" },
  { icon: Eye, label: "Exploded", tool: "exploded" },
  { icon: Scissors, label: "Section", tool: "section" },
];

function LayerControls({
  layerOpacity,
  setLayerOpacity,
  className,
}: {
  layerOpacity: Record<keyof ModelLayerVisibility, number>;
  setLayerOpacity: React.Dispatch<React.SetStateAction<Record<keyof ModelLayerVisibility, number>>>;
  className?: string;
}) {
  const { modelLayers, toggleModelLayer } = useProjectStore();
  const groups = MODEL_LAYER_GROUPS;

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center gap-2 pb-2 border-b border-border">
        <Layers className="h-4 w-4 text-primary" />
        <p className="text-sm font-semibold">Layer Controls</p>
      </div>
      <p className="text-[10px] text-muted-foreground px-1 leading-relaxed">
        Toggle layers and adjust per-layer transparency for structure and excavation meshes.
      </p>
      {groups.map((group) => (
        <div key={group}>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5 px-1">
            {group}
          </p>
          <div className="space-y-2">
            {MODEL_LAYER_DEFS.filter((l) => l.group === group).map(({ key, label }) => (
              <div key={key} className="rounded-md border border-border/50 p-2 space-y-1.5">
                <button
                  type="button"
                  onClick={() => toggleModelLayer(key)}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-md px-1 py-0.5 text-xs transition-all duration-200",
                    modelLayers[key] ? "text-foreground" : "text-muted-foreground",
                  )}
                >
                  <span
                    className={cn(
                      "h-2 w-2 rounded-sm shrink-0",
                      modelLayers[key] ? "bg-primary" : "bg-muted-foreground/30",
                    )}
                  />
                  {label}
                </button>
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="h-3 w-3 text-muted-foreground shrink-0" />
                  <input
                    aria-label={`${label} transparency`}
                    type="range"
                    min={20}
                    max={100}
                    value={layerOpacity[key]}
                    onChange={(e) =>
                      setLayerOpacity((prev) => ({ ...prev, [key]: Number(e.target.value) }))
                    }
                    className="w-full accent-primary"
                  />
                  <span className="font-data text-[10px] text-muted-foreground w-8 text-right">
                    {layerOpacity[key]}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ModelViewerPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { project, modelFile, excavationFile, summaryStats, loading, error, load } =
    useProjectData(projectId);
  const { modelLayers, cesiumTool, setCesiumTool } = useProjectStore();
  const [fullscreen, setFullscreen] = useState(false);
  const [mobileLayersOpen, setMobileLayersOpen] = useState(false);
  const [layerOpacity, setLayerOpacity] = useState<Record<keyof ModelLayerVisibility, number>>(() => {
    const initial = {} as Record<keyof ModelLayerVisibility, number>;
    for (const def of MODEL_LAYER_DEFS) initial[def.key] = 100;
    return initial;
  });

  const modelOpacity = useMemo(() => {
    const active = MODEL_LAYER_DEFS.filter((l) => modelLayers[l.key]);
    if (!active.length) return 1;
    const avg = active.reduce((sum, l) => sum + layerOpacity[l.key], 0) / active.length;
    return avg / 100;
  }, [layerOpacity, modelLayers]);

  if (loading) return <ProjectLoading message="Loading 3D model…" />;
  if (error || !project) return <ProjectError error={error || "Not found"} onRetry={load} />;

  const center: [number, number] = [project.center_lng ?? 77.5946, project.center_lat ?? 12.9716];
  const hasModel = !!modelFile?.file_url;

  return (
    <div
      className={cn(
        "flex-1 flex flex-col min-h-0 bg-background pb-14 md:pb-0",
        fullscreen && "fixed inset-0 z-50 pb-0",
      )}
    >
      <div className="flex-1 flex min-h-0 p-2 gap-2">
        <aside className="w-56 shrink-0 panel-elevated rounded-lg overflow-y-auto hidden md:block">
          <div className="p-3">
            <LayerControls layerOpacity={layerOpacity} setLayerOpacity={setLayerOpacity} />
          </div>
        </aside>

        <div className="flex-1 relative min-w-0 map-viewport overflow-hidden">
          <div className="absolute top-3 left-3 z-20 flex gap-1 panel-glass rounded-md p-1">
            {VIEW_TOOLS.map(({ icon: Icon, label, tool }) => (
              <Button
                key={label}
                variant="ghost"
                size="sm"
                className={cn(
                  "h-7 gap-1 text-[10px] px-2",
                  cesiumTool === tool && "bg-primary/15 text-primary",
                )}
                onClick={() => setCesiumTool(tool)}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </Button>
            ))}
          </div>

          <div className="absolute top-3 right-3 z-20 flex gap-1">
            <Button
              variant="secondary"
              size="sm"
              className="h-8 gap-1 panel-glass md:hidden"
              onClick={() => setMobileLayersOpen((v) => !v)}
            >
              <Layers className="h-3.5 w-3.5" />
              Layers
            </Button>
            <Button
              variant="secondary"
              size="icon"
              className="h-8 w-8 panel-glass"
              onClick={() => setFullscreen((v) => !v)}
              title={fullscreen ? "Exit fullscreen" : "Maximize viewer"}
            >
              {fullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
            </Button>
          </div>

          {mobileLayersOpen && (
            <div className="absolute inset-x-3 top-14 z-30 max-h-[60%] overflow-y-auto rounded-lg border border-border bg-background/95 p-3 shadow-xl md:hidden">
              <LayerControls layerOpacity={layerOpacity} setLayerOpacity={setLayerOpacity} />
            </div>
          )}

          {!hasModel ? (
            <div className="absolute inset-0 flex items-center justify-center bg-background/60 backdrop-blur-sm">
              <Card float className="p-8 text-center max-w-md">
                <Box className="h-12 w-12 text-primary/50 mx-auto mb-4" />
                <p className="font-semibold text-base mb-2">No 3D model generated</p>
                <p className="text-sm text-muted-foreground mb-4">
                  Run AI Design Studio to produce a conceptual GLB model for BIM inspection.
                </p>
                <Badge variant="warning">Preliminary visualization</Badge>
              </Card>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="absolute inset-0"
            >
              <CesiumView
                center={center}
                boundary={project.boundary_geojson}
                alignment={project.alignment_geojson}
                modelUrl={modelFile?.file_url ?? null}
                excavationUrl={excavationFile?.file_url ?? null}
                useModelLayers
                modelOpacity={modelOpacity}
              />
            </motion.div>
          )}
        </div>
      </div>

      {!fullscreen && (
        <>
          <BottomSummaryBar stats={summaryStats} />
        </>
      )}
    </div>
  );
}
