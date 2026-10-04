"use client";

import { useEffect, useState } from "react";
import { ChevronDown, Download, Eye, EyeOff, Focus, Lock, MoreHorizontal, Layers, Map, Trash2, Unlock } from "lucide-react";
import { SCENE3D_LAYER_LABELS, type Scene3DLayerKey } from "@/lib/cesium-scene";
import { extractDesignMeshLayers } from "@/lib/design-mesh-layers";
import { Button } from "@/components/ui/button";
import type { DesignOutput } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useProjectStore } from "@/stores/projectStore";

const SCENE_GROUPS: { label: string; keys: Scene3DLayerKey[] }[] = [
  { label: "Environment", keys: ["terrain", "water", "trees"] },
  { label: "Infrastructure", keys: ["roads", "buildings", "flyover", "bridge", "pipeline", "drainage"] },
  { label: "Analysis", keys: ["excavation", "construction", "labels"] },
];

function LayerRow({
  label,
  sublabel,
  visible,
  onToggle,
  color = "#3B82F6",
  selected,
  locked,
  onSelect,
  onToggleLock,
  indent,
}: {
  label: string;
  sublabel?: string;
  visible: boolean;
  onToggle: () => void;
  color?: string;
  selected?: boolean;
  locked?: boolean;
  onSelect?: () => void;
  onToggleLock?: () => void;
  indent?: boolean;
}) {
  return (
    <div
      className={cn(
        "group flex w-full items-center gap-1.5 rounded-lg border px-2 py-1.5 text-[11px] transition-all",
        indent && "pl-5",
        selected
          ? "border-[rgba(34,211,238,0.38)] bg-[rgba(34,211,238,0.1)] text-foreground"
          : visible
            ? "border-border bg-white/[0.04] text-[#E2E8F0] hover:bg-white/[0.07]"
            : "border-transparent text-muted-foreground hover:bg-surface-hover",
      )}
    >
      <button type="button" onClick={onSelect ?? onToggle} className="flex min-w-0 flex-1 items-center gap-2 text-left">
        <span
          className="h-2.5 w-2.5 shrink-0 rounded-sm border border-white/20"
          style={{ backgroundColor: visible ? color : "rgba(100,116,139,0.28)" }}
          aria-hidden
        />
        <span className="min-w-0 flex-1 truncate">{label}</span>
      </button>
      {sublabel && (
        <span className="shrink-0 text-[9px] text-muted-foreground font-data">{sublabel}</span>
      )}
      <button
        type="button"
        onClick={onToggle}
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-surface-hover hover:text-foreground"
        title={visible ? "Hide layer" : "Show layer"}
      >
        {visible ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
      </button>
      <button
        type="button"
        onClick={onToggleLock}
        className={cn(
          "flex h-5 w-5 shrink-0 items-center justify-center rounded hover:bg-surface-hover",
          locked ? "text-[#F59E0B]" : "text-muted-foreground hover:text-foreground",
        )}
        title={locked ? "Unlock layer" : "Lock layer"}
      >
        {locked ? <Lock className="h-3.5 w-3.5" /> : <Unlock className="h-3.5 w-3.5" />}
      </button>
      <button
        type="button"
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-surface-hover hover:text-foreground"
        title="Layer options"
      >
        <MoreHorizontal className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export default function BlenderLayerPanel({
  design,
  className,
}: {
  design?: DesignOutput | null;
  className?: string;
}) {
  const [expandedLayers, setExpandedLayers] = useState<Record<string, boolean>>({});
  const [showMapContext, setShowMapContext] = useState(false);
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);
  const [lockedLayers, setLockedLayers] = useState<Record<string, boolean>>({});
  const [isolatedSnapshot, setIsolatedSnapshot] = useState<Record<string, boolean> | null>(null);

  const {
    scene3dLayers,
    toggleScene3dLayer,
    setScene3dLayers,
    undergroundView,
    toggleUndergroundView,
    designMeshVisibility,
    toggleDesignMeshLayer,
    syncDesignMeshFromSpec,
  } = useProjectStore();

  useEffect(() => {
    syncDesignMeshFromSpec(design?.geometry_spec ?? null);
  }, [design?.geometry_spec, syncDesignMeshFromSpec]);

  const aiLayers = extractDesignMeshLayers(design?.geometry_spec);

  const layerColor = (id: string) => {
    if (id.includes("deck")) return "#94A3B8";
    if (id.includes("asphalt") || id.includes("road")) return "#1E293B";
    if (id.includes("pier")) return "#60A5FA";
    if (id.includes("foundation") || id.includes("concrete")) return "#A3A3A3";
    if (id.includes("excavation")) return "#F59E0B";
    if (id.includes("drain") || id.includes("pipe")) return "#22D3EE";
    return "#3B82F6";
  };

  const setAllAiLayers = (visible: boolean) => {
    if (!aiLayers.length) return;
    useProjectStore.setState({
      designMeshVisibility: Object.fromEntries(aiLayers.map((group) => [group.id, visible])),
    });
    setIsolatedSnapshot(null);
  };

  const isolateLayer = () => {
    if (!selectedLayer || !aiLayers.length) return;
    if (isolatedSnapshot) {
      useProjectStore.setState({ designMeshVisibility: isolatedSnapshot });
      setIsolatedSnapshot(null);
      return;
    }
    setIsolatedSnapshot(designMeshVisibility);
    useProjectStore.setState({
      designMeshVisibility: Object.fromEntries(aiLayers.map((group) => [group.id, group.id === selectedLayer])),
    });
  };

  const setAllSceneLayers = (visible: boolean) => {
    setScene3dLayers(
      Object.fromEntries(
        SCENE_GROUPS.flatMap((group) => group.keys).map((key) => [key, visible]),
      ) as Partial<Record<Scene3DLayerKey, boolean>>,
    );
  };

  return (
    <div
      className={cn(
        "h-full min-h-0 overflow-y-auto overscroll-contain bg-background-secondary px-3 py-3 space-y-3 border-b border-[rgba(148,163,184,0.1)] scrollbar-thin-dark",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Layers className="h-3.5 w-3.5 text-accent shrink-0" />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              AI Model Layers
            </p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">CAD/GIS generated model manager</p>
          </div>
        </div>
        <span className="rounded-full border border-[rgba(34,211,238,0.25)] bg-[rgba(34,211,238,0.08)] px-2 py-1 text-[9px] text-[#A5F3FC]">
          {aiLayers.length} groups
        </span>
      </div>

      {aiLayers.length === 0 ? (
        <p className="rounded-xl border border-border bg-black/20 px-3 py-3 text-[11px] text-muted-foreground leading-snug">
          Generate a concept model to view bridge deck, piers, foundations, road surface, and excavation volumes.
        </p>
      ) : (
        <div className="space-y-2">
          <div className="grid grid-cols-4 gap-1">
            <Button variant="secondary" size="sm" className="h-7 px-1 text-[10px]" onClick={() => setAllAiLayers(true)}>
              Show all
            </Button>
            <Button variant="secondary" size="sm" className="h-7 px-1 text-[10px]" onClick={() => setAllAiLayers(false)}>
              Hide all
            </Button>
            <Button variant="secondary" size="sm" className="h-7 px-1 text-[10px]" onClick={isolateLayer} disabled={!selectedLayer}>
              <Focus className="h-3 w-3" />
              {isolatedSnapshot ? "Restore" : "Isolate"}
            </Button>
            <Button variant="secondary" size="sm" className="h-7 px-1 text-[10px]" disabled title="Export selected layer unavailable in this build">
              <Download className="h-3 w-3" />
            </Button>
          </div>
          {aiLayers.map((group) => {
            const open = expandedLayers[group.id] ?? false;
            const visible = designMeshVisibility[group.id] !== false;
            const selected = selectedLayer === group.id;
            return (
              <div key={group.id} className="rounded-xl border border-border bg-black/15 p-1">
                <div className="flex items-center gap-0.5">
                  <button
                    type="button"
                    aria-label={open ? "Collapse meshes" : "Expand meshes"}
                    onClick={() =>
                      setExpandedLayers((prev) => ({ ...prev, [group.id]: !open }))
                    }
                    className="shrink-0 p-0.5 text-muted-foreground hover:text-foreground"
                  >
                    <ChevronDown
                      className={cn("h-3 w-3 transition-transform", open && "rotate-180")}
                    />
                  </button>
                  <div className="flex-1 min-w-0">
                    <LayerRow
                      label={group.label}
                      sublabel={`${group.meshCount} mesh${group.meshCount === 1 ? "" : "es"}`}
                      visible={visible}
                      color={layerColor(group.id)}
                      selected={selected}
                      locked={lockedLayers[group.id]}
                      onSelect={() => setSelectedLayer(group.id)}
                      onToggleLock={() =>
                        setLockedLayers((prev) => ({ ...prev, [group.id]: !prev[group.id] }))
                      }
                      onToggle={() => toggleDesignMeshLayer(group.id)}
                    />
                  </div>
                </div>
                {open && (
                  <div className="space-y-0.5 mt-0.5 mb-1">
                    {group.meshes.map((mesh) => (
                      <div
                        key={`${group.id}/${mesh.name}`}
                        className="flex items-center gap-2 pl-8 pr-2 py-0.5 text-[10px] text-muted-foreground font-mono truncate"
                        title={`${mesh.kind} · ${mesh.name}`}
                      >
                        <span className="h-1 w-1 rounded-full bg-muted-foreground/50 shrink-0" />
                        {mesh.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
          <Button
            variant="destructive"
            size="sm"
            className="h-7 w-full text-[10px]"
            disabled
            title="Generated model deletion requires a backend action and is not available in this workspace build"
          >
            <Trash2 className="h-3 w-3" />
            Delete generated model
          </Button>
        </div>
      )}

      <div className="border-t border-border/60 pt-3">
        <button
          type="button"
          onClick={() => setShowMapContext((v) => !v)}
          className="flex w-full items-center gap-2 rounded-lg px-1 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground hover:text-foreground"
        >
          <Map className="h-3 w-3 shrink-0" />
          Map context
          <ChevronDown
            className={cn("h-3 w-3 ml-auto transition-transform", showMapContext && "rotate-180")}
          />
        </button>

        {showMapContext && (
          <div className="space-y-2 mt-1">
            <div className="grid grid-cols-2 gap-1">
              <Button variant="secondary" size="sm" className="h-7 text-[10px]" onClick={() => setAllSceneLayers(true)}>
                Show all
              </Button>
              <Button variant="secondary" size="sm" className="h-7 text-[10px]" onClick={() => setAllSceneLayers(false)}>
                Hide all
              </Button>
            </div>
            {SCENE_GROUPS.map(({ label, keys }) => (
              <div key={label}>
                <p className="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground/80 px-1 mb-0.5">
                  {label}
                </p>
                <div className="space-y-0.5">
                  {keys.map((key) => (
                    <LayerRow
                      key={key}
                      label={SCENE3D_LAYER_LABELS[key]}
                      visible={scene3dLayers[key]}
                      color={
                        key === "water" || key === "drainage" || key === "pipeline"
                          ? "#22D3EE"
                          : key === "excavation" || key === "construction"
                            ? "#F59E0B"
                            : "#3B82F6"
                      }
                      selected={selectedLayer === `scene:${key}`}
                      locked={lockedLayers[`scene:${key}`]}
                      onSelect={() => setSelectedLayer(`scene:${key}`)}
                      onToggleLock={() =>
                        setLockedLayers((prev) => ({ ...prev, [`scene:${key}`]: !prev[`scene:${key}`] }))
                      }
                      onToggle={() => toggleScene3dLayer(key)}
                    />
                  ))}
                </div>
              </div>
            ))}
            <Button
              variant={undergroundView ? "default" : "ghost"}
              size="sm"
              className="w-full h-7 text-[10px]"
              onClick={toggleUndergroundView}
            >
              {undergroundView ? "Underground view on" : "Show underground"}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
