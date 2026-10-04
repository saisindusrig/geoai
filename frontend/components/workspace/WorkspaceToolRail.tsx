"use client";

import {
  AlignHorizontalSpaceAround, Copy, Expand,
  MousePointer2, Move3D, Redo2, RotateCw, Ruler, Scale3D, Trash2, Undo2, SquareDashed, Waypoints,
} from "lucide-react";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import { useEffect, useState } from "react";
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
  { id: "select", label: "Select", hint: "Select / pan map", icon: MousePointer2, mapTool: "select", editorTool: "select" },
  { id: "move", label: "Move", hint: "Move selected component · G", icon: Move3D, editorTool: "translate" },
  { id: "rotate", label: "Rotate", hint: "Rotate selected component · R", icon: RotateCw, editorTool: "rotate" },
  { id: "scale", label: "Scale", hint: "Scale selected component · S", icon: Scale3D, editorTool: "scale" },
];

const surveyTools: RailItem[] = [
  { id: "boundary", label: "Draw boundary", hint: "Draw site boundary", icon: SquareDashed, mapTool: "draw-polygon" },
  { id: "edit-boundary", label: "Edit boundary handles", hint: "Drag boundary vertices", icon: SquareDashed, mapTool: "edit-boundary" },
  { id: "edit-alignment", label: "Edit alignment handles", hint: "Drag alignment vertices", icon: Waypoints, mapTool: "edit-alignment" },
  { id: "alignment", label: "Draw alignment", hint: "Draw alignment", icon: AlignHorizontalSpaceAround, mapTool: "draw-corridor" },
  { id: "measure", label: "Measure", hint: "Measure distance", icon: Ruler, mapTool: "measure-distance" },
  { id: "area", label: "Measure area", hint: "Measure area", icon: Expand, mapTool: "measure-area" },
];

function RailButton({ item, active, onClick, disabled }: { item: RailItem; active?: boolean; onClick: () => void; disabled?: boolean }) {
  const Icon = item.icon;
  return (
    <button type="button" aria-label={item.label} aria-pressed={active ?? false} title={item.hint} disabled={disabled} onClick={onClick}
      className={cn("grid size-10 shrink-0 place-items-center rounded-sm border border-white/10 bg-[#0b1511]/70 text-[#d6e0da] backdrop-blur-sm transition-colors hover:bg-background/90 hover:text-foreground disabled:opacity-35", active && "border-primary/35 bg-primary/15 text-primary shadow-[inset_2px_0_0_var(--primary)]")}>
      <Icon className="size-4" />
    </button>
  );
}

export default function WorkspaceToolRail({ editor }: { editor: EditableModelEditor }) {
  const [measureOpen, setMeasureOpen] = useState(false);
  const { activeTool, activateTool } = useProjectStore();
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLElement && event.target.closest("input, textarea, select, [contenteditable=true]")) return;
      const key = event.key.toLowerCase();
      if (event.ctrlKey || event.metaKey) {
        if (key === "z") { event.preventDefault(); if (event.shiftKey) editor.redo(); else editor.undo(); }
        return;
      }
      const mode = ({ v: "select", g: "translate", r: "rotate", s: "scale" } as const)[key as "v" | "g" | "r" | "s"];
      if (mode) { event.preventDefault(); editor.setTool(mode); activateTool("select"); }
      if (key === "delete") { event.preventDefault(); editor.deleteSelected(); }
      if (key === "f") { event.preventDefault(); window.dispatchEvent(new CustomEvent(editor.selectedIds.length ? "geoai:locate-component" : "geoai:fit-project", {detail:editor.selectedIds[0]})); }
      if (key === "m") { useProjectStore.getState().setScene3dMeasureTool("distance"); setMeasureOpen(true); }
      if (key === "escape") { useProjectStore.getState().setScene3dMeasureTool("none"); setMeasureOpen(false); }
    };
    window.addEventListener("keydown",shortcut);
    return () => window.removeEventListener("keydown",shortcut);
  }, [editor, activateTool]);
  const activate = (item: RailItem) => {
    if (item.id === "measure" || item.id === "area") { setMeasureOpen(true); editor.setTool("select"); useProjectStore.getState().setScene3dMeasureTool(item.id === "area" ? "area" : "distance"); return; }
    useProjectStore.getState().setScene3dMeasureTool("none");
    if (item.editorTool) editor.setTool(item.editorTool);
    if (item.mapTool) { editor.setTool("select"); activateTool(item.mapTool); }
    else activateTool("select");
  };
  return (
    <><aside className="workspace-toolrail flex max-h-[calc(100vh-10rem)] w-10 flex-col items-center gap-1 overflow-y-auto p-0" aria-label="Workspace tools">
      {editTools.map((item) => <RailButton key={item.id} item={item} onClick={() => activate(item)} active={activeTool === "select" && item.editorTool === editor.tool} />)}
      <span className="my-1 h-px w-6 bg-white/10" />
      {surveyTools.map((item) => <RailButton key={item.id} item={item} onClick={() => activate(item)} active={item.mapTool === activeTool} />)}
      <span className="my-1 h-px w-6 bg-white/10" />
      <RailButton item={{ id: "duplicate", label: "Duplicate", hint: "Duplicate selected component", icon: Copy }} onClick={editor.duplicateSelected} disabled={!editor.selectedIds.length} />
      <RailButton item={{ id: "delete", label: "Delete", hint: "Delete selected component · Del", icon: Trash2 }} onClick={editor.deleteSelected} disabled={!editor.selectedIds.length} />
      <span className="my-1 h-px w-6 bg-white/10" />
      <RailButton item={{ id: "undo", label: "Undo", hint: "Undo · Ctrl + Z", icon: Undo2 }} onClick={editor.undo} disabled={!editor.canUndo} />
      <RailButton item={{ id: "redo", label: "Redo", hint: "Redo · Ctrl + Shift + Z", icon: Redo2 }} onClick={editor.redo} disabled={!editor.canRedo} />
    </aside>{measureOpen && <div aria-label="Measurement tools" className="absolute left-12 top-44 z-40 w-40 space-y-1 rounded-sm border border-border bg-background-secondary p-2 shadow-xl">{([ ["distance","Distance"],["height","Elevation"],["slope","Slope"],["area","Area"],["clearance","Clearance"] ] as const).map(([mode,label]) => <button key={mode} className="block w-full px-2 py-2 text-left text-xs hover:bg-primary/10" onClick={()=>{editor.setTool("select"); useProjectStore.getState().setScene3dMeasureTool(mode);}}>{label}</button>)}<button className="block w-full px-2 py-2 text-left text-xs text-muted-foreground" onClick={()=>{setMeasureOpen(false); useProjectStore.getState().setScene3dMeasureTool("none");}}>Cancel · Escape</button></div>}</>
  );
}
