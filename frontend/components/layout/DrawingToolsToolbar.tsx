"use client";

import {
  Activity,
  Calculator,
  ChevronDown,
  FileClock,
  LandPlot,
  Loader2,
  Magnet,
  MousePointer2,
  Pencil,
  Pentagon,
  RectangleHorizontal,
  Route,
  Ruler,
  Scissors,
  Sparkles,
  Spline,
  Trash2,
  Undo2,
  WandSparkles,
} from "lucide-react";
import { useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { type MapTool, useProjectStore } from "@/stores/projectStore";
import type { GeoJSONGeometry, GenerationMode } from "@/lib/types";
import { GENERATION_MODE_LABELS } from "@/lib/generation-job";
import { toast } from "@/lib/toast";
import { verticesToLine, verticesToPolygon } from "@/lib/map-draw";

function ToolbarButton({
  label,
  icon: Icon,
  active,
  onClick,
  disabled,
  hint,
}: {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  active?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  hint?: string;
}) {
  return (
    <button
      type="button"
      title={hint ?? label}
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "h-8 w-8 flex items-center justify-center rounded-lg border transition-all shrink-0 disabled:opacity-35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
        active
          ? "border-primary/50 bg-primary/20 text-foreground shadow-[var(--shadow-glow-primary)]"
          : "border-border bg-background-secondary/90 text-foreground-secondary hover:border-primary/35 hover:bg-primary/10 hover:text-foreground disabled:hover:border-border disabled:hover:bg-background-secondary/90",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
    </button>
  );
}

function ToolGroup({ children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-1.5 shrink-0 rounded-lg border border-[rgba(148,163,184,0.08)] bg-black/10 px-1 py-0.5">
      <div className="flex items-center gap-1">{children}</div>
    </div>
  );
}

function Divider() {
  return <div className="w-px h-7 bg-[rgba(148,163,184,0.16)] shrink-0 mx-0.5" aria-hidden />;
}

function GenerateMenu({
  onGenerate,
  onAnalyze,
  generating,
  generationMode = "balanced",
  onGenerationModeChange,
}: {
  onGenerate?: (mode?: GenerationMode) => void;
  onAnalyze?: () => void;
  generating?: boolean;
  generationMode?: GenerationMode;
  onGenerationModeChange?: (mode: GenerationMode) => void;
}) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ top: number; right: number } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const modes: GenerationMode[] = ["fast_preview", "balanced", "high_detail"];

  const updatePosition = () => {
    const rect = buttonRef.current?.getBoundingClientRect();
    if (!rect) return;
    setPos({
      top: Math.min(rect.bottom + 8, window.innerHeight - 420),
      right: Math.max(12, window.innerWidth - rect.right),
    });
  };

  const openMenu = () => {
    updatePosition();
    setOpen((value) => !value);
  };

  const runGenerate = (mode: GenerationMode = generationMode) => {
    setOpen(false);
    onGenerate?.(mode);
  };

  const items = [
    { label: "Generate flyover concept", icon: WandSparkles, primary: true },
    { label: "Regenerate selected layer", icon: Sparkles },
    { label: "Estimate BOQ", icon: Calculator },
    { label: "Analyze site", icon: Activity, action: onAnalyze },
    { label: "Generate construction sequence", icon: FileClock },
  ];

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        disabled={generating}
        onClick={openMenu}
        className="flex h-8 shrink-0 items-center gap-1.5 rounded-lg border border-primary btn-primary-gradient px-2.5 text-[11px] font-semibold text-primary-foreground shadow-[var(--shadow-glow-primary)] transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 disabled:opacity-60"
        aria-haspopup="menu"
        data-expanded={open ? "true" : "false"}
        title="Generate design"
      >
        {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <WandSparkles className="h-3.5 w-3.5" />}
        <span className="hidden md:inline">{generating ? "Generating" : "Generate"}</span>
        <span className="hidden lg:inline text-[10px] opacity-80">· {GENERATION_MODE_LABELS[generationMode]}</span>
        <ChevronDown className="h-3 w-3 opacity-80" />
      </button>
      {open &&
        pos &&
        typeof document !== "undefined" &&
        createPortal(
          <>
            <button
              type="button"
              className="fixed inset-0 z-[100] cursor-default bg-transparent"
              aria-label="Close generate menu"
              onClick={() => setOpen(false)}
            />
            <div
              role="menu"
              className="fixed z-[101] w-72 rounded-xl border border-border bg-[rgba(11,17,28,0.98)] p-2 shadow-2xl backdrop-blur-xl"
              style={{ top: pos.top, right: pos.right }}
            >
              <div className="px-2 pb-2 pt-1">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Generation mode
                </p>
                <div className="mt-2 grid gap-1">
                  {modes.map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      onClick={() => onGenerationModeChange?.(mode)}
                      className={cn(
                        "rounded-lg border px-2.5 py-2 text-left text-[11px] transition-all",
                        generationMode === mode
                          ? "border-primary/35 bg-primary/10 text-foreground"
                          : "border-transparent text-muted-foreground hover:border-border hover:bg-white/[0.05]",
                      )}
                    >
                      <span className="font-medium">{GENERATION_MODE_LABELS[mode]}</span>
                      <span className="mt-0.5 block text-[10px] text-muted-foreground">
                        {mode === "fast_preview" && "Quick simple model and approximate BOQ"}
                        {mode === "balanced" && "Preview first, then final model (recommended)"}
                        {mode === "high_detail" && "Detailed geometry and BOQ, slower"}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="my-2 h-px bg-[rgba(148,163,184,0.12)]" />
              <div className="px-2 pb-2 pt-1">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  AI generation
                </p>
              </div>
              <div className="space-y-1">
                {items.map(({ label, icon: Icon, action, primary }) => (
                  <button
                    key={label}
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      if (action) {
                        setOpen(false);
                        action();
                        return;
                      }
                      runGenerate(generationMode);
                    }}
                    className={cn(
                      "flex w-full items-center gap-2 rounded-lg border px-2.5 py-2 text-left text-[12px] transition-all",
                      primary
                        ? "border-primary/30 bg-primary/10 text-foreground"
                        : "border-transparent text-foreground-secondary hover:border-border hover:bg-white/[0.05]",
                    )}
                  >
                    <Icon className={cn("h-3.5 w-3.5 shrink-0", primary ? "text-accent" : "text-muted-foreground")} />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
              <div className="mt-2 rounded-lg border border-[rgba(245,158,11,0.2)] bg-[rgba(245,158,11,0.08)] px-2 py-1.5 text-[10px] leading-snug text-[#FCD34D]">
                Final engineering drawings and quantities require survey data and licensed review.
              </div>
            </div>
          </>,
          document.body,
        )}
    </>
  );
}

export type DrawingToolsToolbarProps = {
  projectType?: string;
  boundary?: GeoJSONGeometry | null;
  alignment?: GeoJSONGeometry | null;
  onSaveBoundary?: (g: GeoJSONGeometry) => void | Promise<void>;
  onSaveAlignment?: (g: GeoJSONGeometry) => void | Promise<void>;
  onGenerate?: (mode?: GenerationMode) => void;
  onAnalyze?: () => void;
  generating?: boolean;
  generationMode?: GenerationMode;
  onGenerationModeChange?: (mode: GenerationMode) => void;
};

export default function DrawingToolsToolbar({
  projectType = "flyover",
  onSaveBoundary,
  onSaveAlignment,
  onGenerate,
  onAnalyze,
  generating,
  generationMode = "balanced",
  onGenerationModeChange,
}: DrawingToolsToolbarProps) {
  const {
    activeTool,
    activateTool,
    popDrawVertex,
    clearDrawVertices,
    drawVertices,
    snapEnabled,
    toggleSnap,
    corridorWidthM,
    setCorridorWidthM,
    editVertices,
    revertEditVertices,
    pendingSave,
    setPendingSave,
    measureHistory,
    clearMeasureHistory,
  } = useProjectStore();

  const select = (tool: MapTool, hint?: "flyover" | "pipeline" | "building" | "terrain") => {
    activateTool(tool, hint ?? null);
  };

  const saveEdit = async () => {
    if (activeTool === "edit-boundary" && editVertices.length >= 3) {
      await onSaveBoundary?.(verticesToPolygon(editVertices));
      activateTool("select");
    } else if (activeTool === "edit-alignment" && editVertices.length >= 2) {
      await onSaveAlignment?.(verticesToLine(editVertices));
      activateTool("select");
    }
  };

  const confirmPending = async () => {
    if (!pendingSave) return;
    if (pendingSave.kind === "boundary") await onSaveBoundary?.(pendingSave.geometry);
    else await onSaveAlignment?.(pendingSave.geometry);
    setPendingSave(null);
    activateTool("select");
  };

  const copyMeasure = (value: string) => {
    void navigator.clipboard.writeText(value);
    toast("Copied", { variant: "success" });
  };

  return (
    <div className="flex min-w-0 flex-nowrap items-center gap-2 overflow-x-auto">
      <ToolGroup label="Select">
        <ToolbarButton
          label="Select"
          icon={MousePointer2}
          active={activeTool === "select"}
          onClick={() => select("select")}
          hint="Select / pan map"
        />
        <ToolbarButton
          label="Smart Suggest"
          icon={Sparkles}
          active={activeTool === "suggest-site"}
          onClick={() => select("suggest-site")}
          hint="AI site suggestions"
        />
        <ToolbarButton
          label="Snap"
          icon={Magnet}
          active={snapEnabled}
          onClick={toggleSnap}
          hint={`Snap: ${snapEnabled ? "on" : "off"}`}
        />
      </ToolGroup>

      <Divider />

      <ToolGroup label="Site">
        <ToolbarButton
          label="Rectangle site"
          icon={RectangleHorizontal}
          active={activeTool === "draw-rectangle"}
          onClick={() => select("draw-rectangle", projectType === "building" ? "building" : undefined)}
          hint="Rectangle site"
        />
        <ToolbarButton
          label="Draw boundary"
          icon={Pentagon}
          active={activeTool === "draw-polygon"}
          onClick={() => select("draw-polygon")}
          hint="Draw site boundary"
        />
        <ToolbarButton
          label="Corridor"
          icon={Route}
          active={activeTool === "draw-corridor"}
          onClick={() => select("draw-corridor")}
          hint="Draw alignment"
        />
        <ToolbarButton
          label="Road / line"
          icon={Spline}
          active={activeTool === "draw-line"}
          onClick={() => select("draw-line")}
          hint="Draw road centerline"
        />
        <ToolbarButton
          label="Edit boundary"
          icon={Pencil}
          active={activeTool === "edit-boundary"}
          onClick={() => select("edit-boundary")}
          hint="Edit vertices"
        />
        <ToolbarButton
          label="Edit alignment"
          icon={Scissors}
          active={activeTool === "edit-alignment"}
          onClick={() => select("edit-alignment")}
          hint="Split alignment"
        />
        <ToolbarButton
          label="Undo vertex"
          icon={Undo2}
          disabled={drawVertices.length === 0}
          onClick={() => popDrawVertex()}
          hint="Undo last vertex"
        />
        <ToolbarButton
          label="Clear draw"
          icon={Trash2}
          onClick={() => {
            clearDrawVertices();
            setPendingSave(null);
            activateTool("select");
          }}
          hint="Clear drawing"
        />
      </ToolGroup>

      <Divider />

      <ToolGroup label="Measure">
        <ToolbarButton
          label="Measure distance"
          icon={Ruler}
          active={activeTool === "measure-distance"}
          onClick={() => select("measure-distance")}
          hint="Measure distance"
        />
        <ToolbarButton
          label="Measure area"
          icon={LandPlot}
          active={activeTool === "measure-area"}
          onClick={() => select("measure-area")}
          hint="Measure area"
        />
      </ToolGroup>

      <Divider />

      {onGenerate && <ToolGroup label="Generate">
        <GenerateMenu
          onGenerate={onGenerate}
          onAnalyze={onAnalyze}
          generating={generating}
          generationMode={generationMode}
          onGenerationModeChange={onGenerationModeChange}
        />
      </ToolGroup>}

      {activeTool === "draw-corridor" && (
        <div className="flex items-center gap-1.5 shrink-0 ml-1 rounded-lg border border-[rgba(148,163,184,0.14)] bg-background-secondary/90 px-2 py-0.5">
          <span className="text-[10px] text-muted-foreground">Width m</span>
          <Input
            type="number"
            min={5}
            max={200}
            value={corridorWidthM}
            onChange={(e) => setCorridorWidthM(Number(e.target.value) || 30)}
            className="h-7 w-16 border-border bg-background text-xs"
          />
        </div>
      )}

      {(activeTool === "edit-boundary" || activeTool === "edit-alignment") && (
        <div className="flex items-center gap-1 shrink-0">
          <Button size="sm" className="h-7 text-xs" onClick={() => void saveEdit()}>
            Save
          </Button>
          <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={revertEditVertices}>
            Revert
          </Button>
        </div>
      )}

      {pendingSave && (
        <Button size="sm" className="h-7 text-xs shrink-0" onClick={() => void confirmPending()}>
          Confirm save
        </Button>
      )}

      {measureHistory.length > 0 && (
        <div className="flex items-center gap-1 shrink-0 ml-auto">
          {measureHistory.slice(0, 2).map((m) => (
            <button
              key={m.id}
              type="button"
              title="Copy measurement"
              onClick={() => copyMeasure(m.value)}
              className="max-w-[110px] truncate rounded-lg border border-border bg-background-secondary/90 px-1.5 py-0.5 text-[10px] text-muted-foreground hover:text-foreground"
            >
              {m.kind === "distance" ? "↔" : "▦"} {m.value}
            </button>
          ))}
          <button
            type="button"
            title="Clear measure history"
            onClick={clearMeasureHistory}
            className="text-[10px] text-muted-foreground hover:text-foreground px-1.5"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
}
