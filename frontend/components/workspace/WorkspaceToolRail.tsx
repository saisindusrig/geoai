"use client";

import {
  Copy, Focus, MousePointer2, Move3D, Pentagon, Pencil, Redo2,
  RotateCw, Route, Ruler, Scale3D, Trash2, Undo2, Waypoints,
} from "lucide-react";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import { useEffect, useId, useState } from "react";
import { cn } from "@/lib/utils";
import { useProjectStore, type MapTool } from "@/stores/projectStore";

type RailItem = {
  id: string;
  label: string;
  hint: string;
  icon: React.ComponentType<{ className?: string }>;
  mapTool?: MapTool;
  editorTool?: "select" | "translate" | "rotate" | "scale";
};

const editTools: RailItem[] = [
  { id: "select", label: "Select object", hint: "Select an object · V", icon: MousePointer2, mapTool: "select", editorTool: "select" },
  { id: "move", label: "Move selection", hint: "Move selected objects · G", icon: Move3D, editorTool: "translate" },
  { id: "rotate", label: "Rotate selection", hint: "Rotate selected objects · R", icon: RotateCw, editorTool: "rotate" },
  { id: "scale", label: "Scale selection", hint: "Scale selected objects · S", icon: Scale3D, editorTool: "scale" },
];

const surveyTools: RailItem[] = [
  { id: "boundary", label: "Draw site boundary", hint: "Draw a closed site boundary", icon: Pentagon, mapTool: "draw-polygon" },
  { id: "edit-boundary", label: "Edit site boundary", hint: "Drag existing boundary vertices", icon: Pencil, mapTool: "edit-boundary" },
  { id: "alignment", label: "Draw alignment", hint: "Draw a road or infrastructure centerline", icon: Route, mapTool: "draw-line" },
  { id: "edit-alignment", label: "Edit alignment", hint: "Drag existing alignment vertices", icon: Waypoints, mapTool: "edit-alignment" },
];

const measurements = [
  ["distance", "Distance", "Pick two points"],
  ["height", "Elevation", "Pick one surface point"],
  ["slope", "Slope", "Pick start and end"],
  ["area", "Area", "Pick polygon vertices"],
  ["clearance", "Clearance", "Pick two facing surfaces"],
] as const;

function RailButton({ item, active, onClick, disabled, disabledReason }: {
  item: RailItem; active?: boolean; onClick: () => void; disabled?: boolean; disabledReason?: string;
}) {
  const Icon = item.icon;
  const hintId = useId();
  const description = disabled && disabledReason ? `${item.label} · ${disabledReason}` : item.hint;
  return (
    <span title={description} className="block shrink-0">
      <button type="button" aria-label={item.label} aria-describedby={hintId} aria-pressed={active}
        disabled={disabled} onClick={onClick}
        className={cn("grid size-10 place-items-center rounded-sm border border-white/10 bg-[#0b1511]/70 text-[#d6e0da] backdrop-blur-sm transition-colors hover:bg-background/90 hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-35", active && "border-primary/35 bg-primary/15 text-primary shadow-[inset_2px_0_0_var(--primary)]")}>
        <Icon className="size-4" />
      </button>
      <span id={hintId} className="sr-only">{description}</span>
    </span>
  );
}

export default function WorkspaceToolRail({ editor }: { editor: EditableModelEditor }) {
  const [measureOpen, setMeasureOpen] = useState(false);
  const [surveyOpen, setSurveyOpen] = useState(false);
  const activeTool = useProjectStore(state => state.activeTool);
  const activateTool = useProjectStore(state => state.activateTool);
  const measureMode = useProjectStore(state => state.scene3dMeasureTool);
  const vertices = useProjectStore(state => state.drawVertices);
  const unit = useProjectStore(state => state.measureUnit);
  const boundary = useProjectStore(state => state.drawnBoundary ?? state.project?.boundary_geojson);
  const alignment = useProjectStore(state => state.drawnAlignment ?? state.project?.alignment_geojson);
  const hasEditableSelection = Boolean(editor.document?.components.some(component => editor.selectedIds.includes(component.id) && !component.locked));
  const selectionHint = editor.selectedIds.length ? "Unlock a selected object to edit it" : "Select an editable object first";
  const drawing = activeTool.startsWith("draw-") || activeTool.startsWith("edit-");
  const pendingSave = useProjectStore(state => state.pendingSave);

  const resetTools = () => {
    setMeasureOpen(false);
    setSurveyOpen(false);
    useProjectStore.getState().setScene3dMeasureTool("none");
    activateTool("select");
    editor.setTool("select");
  };
  const startMeasurement = () => {
    resetTools();
    useProjectStore.getState().setScene3dMeasureTool("distance");
    setMeasureOpen(true);
  };
  const frameView = () => {
    window.dispatchEvent(new CustomEvent(editor.selectedIds.length ? "geoai:locate-component" : "geoai:fit-project", { detail: editor.selectedIds[0] }));
  };

  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.target instanceof HTMLElement && event.target.closest("input, textarea, select, [contenteditable]:not([contenteditable=false]), [role=dialog]")) return;
      const key = event.key.toLowerCase();
      if (key === "escape") { resetTools(); return; }
      if (event.ctrlKey || event.metaKey) {
        if (key === "z") {
          event.preventDefault();
          if (drawing) {
            if (!event.shiftKey && activeTool.startsWith("draw-")) useProjectStore.getState().popDrawVertex();
          } else if (event.shiftKey) editor.redo();
          else editor.undo();
        }
        return;
      }
      if (event.altKey || event.repeat) return;
      const mode = ({ v: "select", g: "translate", r: "rotate", s: "scale" } as const)[key as "v" | "g" | "r" | "s"];
      if (mode) {
        if (mode !== "select" && !hasEditableSelection) return;
        event.preventDefault(); resetTools(); editor.setTool(mode);
      }
      if (key === "delete" && hasEditableSelection && !drawing && measureMode === "none") { event.preventDefault(); editor.deleteSelected(); }
      if (key === "f") { event.preventDefault(); frameView(); }
      if (key === "m") { event.preventDefault(); startMeasurement(); }
    };
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  });

  const activate = (item: RailItem) => {
    resetTools();
    if (item.mapTool) { activateTool(item.mapTool); setSurveyOpen(item.mapTool !== "select"); }
    else if (item.editorTool) editor.setTool(item.editorTool);
  };

  return (
    <>
      <aside className="workspace-toolrail flex max-h-[calc(100vh-10rem)] w-10 flex-col items-center gap-1 overflow-y-auto p-0" aria-label="Workspace tools">
        <div role="group" aria-label="Object editing" className="flex flex-col gap-1">
          {editTools.map(item => <RailButton key={item.id} item={item} onClick={() => activate(item)}
            active={measureMode === "none" && activeTool === "select" && item.editorTool === editor.tool}
            disabled={item.id !== "select" && !hasEditableSelection} disabledReason={selectionHint} />)}
        </div>
        <span aria-hidden="true" className="my-1 h-px w-6 bg-white/10" />
        <div role="group" aria-label="Site geometry" className="flex flex-col gap-1">
          {surveyTools.map(item => <RailButton key={item.id} item={item} onClick={() => activate(item)} active={item.mapTool === activeTool}
            disabled={item.id === "edit-boundary" ? !boundary : item.id === "edit-alignment" ? !alignment : false}
            disabledReason={item.id === "edit-boundary" ? "Draw a site boundary first" : "Draw an alignment first"} />)}
        </div>
        <span aria-hidden="true" className="my-1 h-px w-6 bg-white/10" />
        <RailButton item={{ id: "measure", label: "Measure", hint: "Measure distance, elevation, slope, area or clearance · M", icon: Ruler }} active={measureMode !== "none"}
          onClick={() => measureMode !== "none" ? resetTools() : startMeasurement()} />
        <RailButton item={{ id: "frame", label: editor.selectedIds.length ? "Frame selection" : "Fit project", hint: editor.selectedIds.length ? "Focus the selected object · F" : "Fit the project in view · F", icon: Focus }} onClick={frameView} />
        <span aria-hidden="true" className="my-1 h-px w-6 bg-white/10" />
        <RailButton item={{ id: "duplicate", label: "Duplicate selection", hint: "Duplicate selected objects", icon: Copy }} onClick={editor.duplicateSelected} disabled={!hasEditableSelection} disabledReason={selectionHint} />
        <RailButton item={{ id: "delete", label: "Delete selection", hint: "Delete selected objects · Del", icon: Trash2 }} onClick={editor.deleteSelected} disabled={!hasEditableSelection} disabledReason={selectionHint} />
        <span aria-hidden="true" className="my-1 h-px w-6 bg-white/10" />
        <RailButton item={{ id: "undo", label: "Undo", hint: "Undo object edit · Ctrl / Cmd + Z", icon: Undo2 }} onClick={editor.undo} disabled={drawing || !editor.canUndo} disabledReason={drawing ? "Finish drawing before undoing object edits" : "No object edits to undo"} />
        <RailButton item={{ id: "redo", label: "Redo", hint: "Redo object edit · Ctrl / Cmd + Shift + Z", icon: Redo2 }} onClick={editor.redo} disabled={drawing || !editor.canRedo} disabledReason={drawing ? "Finish drawing before redoing object edits" : "No object edits to redo"} />
      </aside>
      {surveyOpen && drawing && <div aria-label="Drawing tool options" className="absolute left-12 top-44 z-40 w-52 space-y-2 border border-border bg-background-secondary p-3 shadow-xl">
        <p className="text-xs font-semibold">{surveyTools.find(item => item.mapTool === activeTool)?.label}</p>
        <p className="text-[10px] text-muted-foreground">{activeTool.startsWith("edit-") ? "Drag vertices. Press Enter to finish, then Save to keep your changes." : "Click to place vertices. Press Enter or double-click to finish, then Save."}</p>
        {!activeTool.startsWith("edit-") && <div className="flex items-center justify-between text-[10px]"><span>{vertices.length} vertices</span><button type="button" disabled={!vertices.length} className="text-primary disabled:opacity-35" onClick={() => useProjectStore.getState().popDrawVertex()}>Undo vertex</button></div>}
        <button type="button" disabled={vertices.length < (activeTool === "draw-polygon" || activeTool === "edit-boundary" ? 3 : 2)} className="block w-full border border-primary/30 bg-primary/15 px-2 py-1.5 text-xs text-primary disabled:opacity-35" onClick={() => window.dispatchEvent(new CustomEvent("geoai:finish-drawing"))}>Finish drawing</button>
        <button type="button" className="text-[10px] text-muted-foreground" onClick={resetTools}>Cancel drawing · Esc</button>
      </div>}
      {pendingSave && !drawing && measureMode === "none" && <p role="status" className="absolute left-12 top-44 z-40 w-52 border border-primary/25 bg-background-secondary p-3 text-xs">{pendingSave.kind === "boundary" ? "Site boundary" : "Alignment"} ready. Use Save to keep your changes.</p>}
      {measureOpen && measureMode !== "none" && <div aria-label="Measurement tools" className="absolute left-12 top-44 z-40 w-52 space-y-1 rounded-sm border border-border bg-background-secondary p-2 shadow-xl">
        <div className="flex items-center justify-between px-2 py-1 text-xs"><strong>Measure</strong><button type="button" aria-label="Toggle measurement units" className="text-primary" onClick={() => useProjectStore.getState().toggleMeasureUnit()}>{unit}</button></div>
        {measurements.map(([mode, label, hint]) => <button type="button" key={mode} aria-pressed={measureMode === mode} className={cn("block w-full px-2 py-1.5 text-left text-xs hover:bg-primary/10", measureMode === mode && "bg-primary/10 text-primary")} onClick={() => { editor.setTool("select"); activateTool("select"); useProjectStore.getState().setScene3dMeasureTool(mode); }}>{label}<span className="mt-0.5 block text-[9px] text-muted-foreground">{hint}</span></button>)}
        <button type="button" className="block w-full px-2 py-2 text-left text-xs text-muted-foreground" onClick={resetTools}>Stop measuring · Esc</button>
      </div>}
    </>
  );
}
