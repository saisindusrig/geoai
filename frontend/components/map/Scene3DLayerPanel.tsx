"use client";

import { Layers, Eye, EyeOff } from "lucide-react";
import { SCENE3D_LAYER_LABELS, type Scene3DLayerKey } from "@/lib/cesium-scene";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { type Scene3DMeasureTool, useProjectStore } from "@/stores/projectStore";

const LAYER_ORDER: Scene3DLayerKey[] = [
  "terrain",
  "roads",
  "buildings",
  "flyover",
  "bridge",
  "pipeline",
  "drainage",
  "excavation",
  "construction",
  "water",
  "trees",
  "labels",
];

const MEASURE_TOOLS: { id: Scene3DMeasureTool; label: string }[] = [
  { id: "distance", label: "Distance" },
  { id: "area", label: "Area" },
  { id: "height", label: "Height" },
  { id: "slope", label: "Slope" },
  { id: "depth", label: "Dig depth" },
];

export default function Scene3DLayerPanel({ compact }: { compact?: boolean }) {
  const { scene3dLayers, toggleScene3dLayer, undergroundView, toggleUndergroundView, scene3dMeasureTool, setScene3dMeasureTool, scene3dMeasureReadout } =
    useProjectStore();

  return (
    <div className={cn("space-y-3", compact && "space-y-2")}>
      <div className="flex items-center gap-2 px-1">
        <Layers className="h-3.5 w-3.5 text-primary" />
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          3D Object Layers
        </p>
      </div>

      <div className="space-y-0.5 max-h-[220px] overflow-y-auto pr-1">
        {LAYER_ORDER.map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => toggleScene3dLayer(key)}
            className={cn(
              "flex w-full items-center gap-2 rounded-md px-2 py-1 text-[11px] transition-colors",
              scene3dLayers[key]
                ? "text-foreground bg-primary/10"
                : "text-muted-foreground hover:bg-muted",
            )}
          >
            {scene3dLayers[key] ? (
              <Eye className="h-3 w-3 shrink-0 text-primary" />
            ) : (
              <EyeOff className="h-3 w-3 shrink-0" />
            )}
            {SCENE3D_LAYER_LABELS[key]}
          </button>
        ))}
      </div>

      <Button
        variant={undergroundView ? "default" : "ghost"}
        size="sm"
        className="w-full h-7 text-[10px]"
        onClick={toggleUndergroundView}
      >
        {undergroundView ? "Underground view on" : "Show underground"}
      </Button>

      <div className="border-t border-border/60 pt-2 space-y-1">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground px-1">
          3D Measure
        </p>
        <div className="flex flex-wrap gap-1">
          {MEASURE_TOOLS.map(({ id, label }) => (
            <Button
              key={id}
              variant={scene3dMeasureTool === id ? "default" : "ghost"}
              size="sm"
              className="h-6 px-2 text-[10px]"
              onClick={() => setScene3dMeasureTool(scene3dMeasureTool === id ? "none" : id)}
            >
              {label}
            </Button>
          ))}
        </div>
        {scene3dMeasureReadout && (
          <p className="text-[10px] text-accent font-data px-1 pt-1">{scene3dMeasureReadout}</p>
        )}
      </div>
    </div>
  );
}
