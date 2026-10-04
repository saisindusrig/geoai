"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Box, Copy, Download, Eye, EyeOff, Grid3X3, LocateFixed, Lock, Map, MousePointer2, Move3D, Plus, Redo2, RotateCw, Save, Scale3D, Search, Trash2, Undo2, Unlock, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import type { EditableModelComponent, Project, StructuralElementType } from "@/lib/types";
import { COMPONENT_SIZES, emptySandboxDocument, parseSandboxPayload, sandboxPayload, SANDBOX_LAYOUT_KEY, type SandboxPayload } from "@/lib/local-sandbox";
import { cn, formatCurrency, formatQty } from "@/lib/utils";

const SandboxGrid = dynamic(() => import("./SandboxGrid"), { ssr: false, loading: () => <div className="grid h-full place-items-center text-sm text-muted-foreground">Opening 3D grid…</div> });
const CesiumView = dynamic(() => import("@/components/map/CesiumView"), { ssr: false, loading: () => <div className="grid h-full place-items-center text-sm text-muted-foreground">Opening map…</div> });
const tools = [
  { id: "select", label: "Select", icon: MousePointer2, shortcut: "V" },
  { id: "translate", label: "Move", icon: Move3D, shortcut: "G" },
  { id: "rotate", label: "Rotate", icon: RotateCw, shortcut: "R" },
  { id: "scale", label: "Scale", icon: Scale3D, shortcut: "S" },
] as const;

function download(data: string, name: string) {
  const url = URL.createObjectURL(new Blob([data], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url; link.download = name; link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Numeric({ label, displayLabel, compact, value, onChange, positive, disabled, step = 0.1 }: { label: string; displayLabel?: string; compact?: boolean; value: number; onChange: (v: number) => void; positive?: boolean; disabled?: boolean; step?: number }) {
  return <label className="flex min-w-0 flex-col gap-1 text-[10px] text-muted-foreground"><span className={compact ? "sr-only" : undefined}>{displayLabel ?? label}</span><input aria-label={label} key={`${label}-${value}`} type="number" defaultValue={Number(value.toFixed(4))} step={step} min={positive ? 0.01 : undefined} disabled={disabled} className="h-8 min-w-0 rounded-sm border border-border bg-background px-2 text-xs text-foreground outline-none focus:border-primary disabled:opacity-40" onBlur={(event) => {
    const n = event.currentTarget.valueAsNumber;
    if (Number.isFinite(n) && (!positive || n > 0)) { if (n !== value) onChange(n); }
    else event.currentTarget.value = String(value);
  }} onKeyDown={(event) => { if (event.key === "Enter") event.currentTarget.blur(); }} /></label>;
}

function VectorFields({ label, values, names = ["East", "North", "Up"], onChange, positive, disabled }: { label: string; values: [number, number, number]; names?: string[]; onChange: (v: [number, number, number]) => void; positive?: boolean; disabled?: boolean }) {
  return <section className="space-y-2"><p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">{label}</p><div className="grid grid-cols-3 gap-2">{names.map((name, i) => <Numeric key={name} label={`${label} ${name}`} displayLabel={name} value={values[i]} positive={positive} disabled={disabled} onChange={(v) => { const next = [...values] as [number, number, number]; next[i] = v; onChange(next); }} />)}</div></section>;
}

function Inspector({ component, editor }: { component: EditableModelComponent; editor: EditableModelEditor }) {
  const update = (changes: Partial<EditableModelComponent>) => editor.updateComponent(component.id, changes);
  const geometry = component.geometry;
  return <div className="space-y-4 p-3">
    <div className="flex items-center justify-between"><p className="text-[10px] font-semibold uppercase tracking-widest text-primary">Properties</p><span className="text-[10px] text-muted-foreground">{component.category.replaceAll("_", " ")}</span></div>
    <label className="block space-y-1 text-[10px] text-muted-foreground"><span>Name</span><input aria-label="Component name" className="h-9 w-full rounded-sm border border-border bg-background px-2 text-xs text-foreground" value={component.name} disabled={component.locked} onChange={(e) => update({ name: e.target.value })} /></label>
    {component.locked && <p className="text-xs text-muted-foreground">Unlock this component to edit it.</p>}
    {editor.selectedIds.length > 1 && <p className="text-xs text-muted-foreground">Handles affect {editor.selectedIds.length} selected objects. These fields edit {component.name}.</p>}
    <VectorFields label="Position (m)" values={component.transform.position} disabled={component.locked} onChange={(position) => update({ transform: { ...component.transform, position } })} />
    <VectorFields label="Rotation (°)" names={["X", "Y", "Z"]} values={component.transform.rotation_deg} disabled={component.locked} onChange={(rotation_deg) => update({ transform: { ...component.transform, rotation_deg } })} />
    <VectorFields label="Scale" names={["X", "Y", "Z"]} values={component.transform.scale} positive disabled={component.locked} onChange={(scale) => update({ transform: { ...component.transform, scale } })} />
    {(geometry.kind === "box" || geometry.kind === "extrusion") && <VectorFields label="Dimensions (m)" names={["Width", "Length", "Height"]} values={geometry.size} positive disabled={component.locked} onChange={(size) => update({ geometry: { ...geometry, size } })} />}
    {(geometry.kind === "cylinder" || geometry.kind === "sweep") && <>
      <VectorFields label="Start (m)" values={geometry.start} disabled={component.locked} onChange={(start) => { if (start.some((n, i) => n !== geometry.end[i])) update({ geometry: { ...geometry, start } }); }} />
      <VectorFields label="End (m)" values={geometry.end} disabled={component.locked} onChange={(end) => { if (end.some((n, i) => n !== geometry.start[i])) update({ geometry: { ...geometry, end } }); }} />
      <Numeric label="Radius (m)" value={geometry.radius_m} positive disabled={component.locked} onChange={(radius_m) => update({ geometry: { ...geometry, radius_m } })} />
    </>}
    <label className="flex items-center justify-between text-xs text-muted-foreground">Color<input aria-label="Component color" type="color" value={component.material.color} disabled={component.locked} className="h-8 w-12 cursor-pointer rounded border border-border bg-background" onChange={(e) => update({ material: { ...component.material, color: e.target.value } })} /></label>
    <div className="grid grid-cols-2 gap-2"><Button size="sm" variant="secondary" onClick={editor.duplicateSelected} disabled={component.locked}><Copy className="size-3" />Duplicate</Button><Button size="sm" variant="outline" onClick={editor.deleteSelected} disabled={component.locked}><Trash2 className="size-3" />Delete</Button></div>
  </div>;
}

export default function SandboxWorkspace({ project, editor }: { project: Project; editor: EditableModelEditor }) {
  const [query, setQuery] = useState("");
  const [placement, setPlacement] = useState<StructuralElementType | null>(null);
  const [fit, setFit] = useState({ sequence: 0, selected: false });
  const [pending, setPending] = useState<{ payload: SandboxPayload; title: string } | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [showOrigin, setShowOrigin] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const onPlaced = useCallback(() => setPlacement(null), []);
  const types = (Object.keys(COMPONENT_SIZES) as StructuralElementType[]).filter((kind) => kind.replaceAll("_", " ").includes(query.toLowerCase()));
  const mapCenter = useMemo<[number, number]>(() => [editor.document?.origin.lng ?? 77.5946, editor.document?.origin.lat ?? 12.9716], [editor.document?.origin.lng, editor.document?.origin.lat]);
  const requestFit = (selected: boolean) => setFit((current) => ({ sequence: current.sequence + 1, selected }));
  useEffect(() => {
    const shortcuts = (event: KeyboardEvent) => {
      if (pending || (event.target instanceof HTMLElement && (event.target.isContentEditable || event.target.closest("input, textarea, select")))) return;
      const command = event.ctrlKey || event.metaKey;
      const key = event.key.toLowerCase();
      if (command && key === "z") { event.preventDefault(); if (event.shiftKey) editor.redo(); else editor.undo(); }
      else if (command && key === "y") { event.preventDefault(); editor.redo(); }
      else if (command && key === "s") { event.preventDefault(); void editor.save().catch(() => undefined); }
      else if (command && key === "d") { event.preventDefault(); editor.duplicateSelected(); }
      else if (!command && (key === "delete" || key === "backspace")) { event.preventDefault(); editor.deleteSelected(); }
      else if (!command && key === "escape") setPlacement(null);
      else if (!command) {
        const tool = tools.find((item) => item.shortcut.toLowerCase() === key);
        if (tool) { editor.setTool(tool.id); setPlacement(null); }
      }
    };
    window.addEventListener("keydown", shortcuts);
    return () => window.removeEventListener("keydown", shortcuts);
  }, [editor, pending]);

  const importFile = async (file: File) => {
    try {
      if (file.size > 10 * 1024 * 1024) throw new Error("Choose a sandbox backup smaller than 10 MB.");
      const payload = parseSandboxPayload(JSON.parse(await file.text()));
      setPending({ payload, title: "Import this layout?" });
      setFileError(null);
    } catch (error) { setFileError(error instanceof Error ? error.message : "Unable to read this file."); }
  };
  if (!editor.document) return <div className="grid flex-1 place-items-center text-sm text-muted-foreground">Restoring sandbox…</div>;
  const doc = editor.document;
  const status = editor.localSaveStatus === "saving" ? "Saving…" : editor.localSaveStatus === "failed" ? "Save failed" : "Saved locally";
  return <div className="flex min-h-0 flex-1 flex-col overflow-hidden bg-background" aria-label="Local sandbox editor">
    <div className="flex flex-wrap items-center gap-2 border-b border-border bg-background-secondary px-3 py-2">
      <div className="flex rounded-sm border border-border p-0.5">{(["grid", "map"] as const).map((view) => <Button key={view} size="sm" variant={editor.sandboxView === view ? "accent" : "ghost"} className="h-8" onClick={() => { editor.setSandboxView(view); setPlacement(null); }}>{view === "grid" ? <Grid3X3 className="size-3.5" /> : <Map className="size-3.5" />}{view === "grid" ? "Grid" : "Map"}</Button>)}</div>
      <div className="flex gap-0.5">{tools.map(({ id, label, icon: Icon, shortcut }) => <Button key={id} size="icon" variant={editor.tool === id && !placement ? "accent" : "ghost"} className="size-8" title={`${label} · ${shortcut}`} aria-label={label} disabled={id !== "select" && !editor.selectedIds.length} onClick={() => { editor.setTool(id); setPlacement(null); }}><Icon className="size-4" /></Button>)}</div>
      <span className="mx-1 h-5 w-px bg-border" />
      <Button size="icon" variant="ghost" className="size-8" title="Undo · Ctrl Z" aria-label="Undo" disabled={!editor.canUndo} onClick={editor.undo}><Undo2 className="size-4" /></Button>
      <Button size="icon" variant="ghost" className="size-8" title="Redo · Ctrl Shift Z" aria-label="Redo" disabled={!editor.canRedo} onClick={editor.redo}><Redo2 className="size-4" /></Button>
      <Button size="sm" variant="ghost" className="h-8 text-xs" onClick={() => requestFit(false)}><LocateFixed className="size-3.5" />Fit all</Button>
      <Button size="sm" variant="ghost" className="h-8 text-xs" disabled={!editor.selectedIds.length || editor.sandboxView === "map"} onClick={() => requestFit(true)}>Fit selected</Button>
      <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground"><span>Snap (m)</span><div className="w-16"><Numeric compact label="Snap meters" value={editor.snapMeters} positive step={0.5} onChange={editor.setSnapMeters} /></div></div>
      <div className="ml-auto flex items-center gap-1">
        <Button size="icon" variant="ghost" className="size-8" title="Download backup" aria-label="Download backup" onClick={() => download(JSON.stringify(sandboxPayload(doc, editor.sandboxView, editor.localDraft), null, 2), "sandbox-layout.json")}><Download className="size-4" /></Button>
        <Button size="icon" variant="ghost" className="size-8" title="Import backup" aria-label="Import backup" onClick={() => inputRef.current?.click()}><Upload className="size-4" /></Button>
        <Button size="sm" variant="outline" className="h-8 text-xs" onClick={() => { const empty = emptySandboxDocument(project); empty.origin = { ...doc.origin }; setPending({ title: "Start a new layout?", payload: sandboxPayload(empty, "grid", editor.localDraft) }); }}><Plus className="size-3" />New layout</Button>
      </div>
      <input ref={inputRef} type="file" accept=".json,application/json" aria-label="Sandbox backup file" className="hidden" onChange={(e) => { const file = e.target.files?.[0]; if (file) void importFile(file); e.target.value = ""; }} />
    </div>
    {(editor.localSaveError || fileError) && <div role="alert" className="flex flex-wrap items-center gap-3 border-b border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs text-amber-200"><span className="flex-1">{fileError ?? editor.localSaveError} {editor.restoreError && `(${editor.restoreError})`}</span>{editor.restoreError && <Button variant="outline" size="sm" onClick={() => { try { const raw = window.localStorage.getItem(SANDBOX_LAYOUT_KEY); if (raw) download(raw, "sandbox-recovery.json"); } catch { setFileError("Saved data cannot be accessed. Download the current layout instead."); } }}>Download saved data</Button>}<Button variant="ghost" size="sm" onClick={() => download(JSON.stringify(sandboxPayload(doc, editor.sandboxView, editor.localDraft), null, 2), "sandbox-layout.json")}>Download current layout</Button>{fileError && <button aria-label="Dismiss import error" onClick={() => setFileError(null)}><X className="size-4" /></button>}</div>}
    <div className="flex min-h-0 flex-1">
      <aside className="flex w-40 shrink-0 flex-col border-r border-border bg-background-secondary lg:w-48" aria-label="Component palette">
        <div className="space-y-2 border-b border-border p-3"><p className="text-[10px] font-semibold uppercase tracking-widest text-primary">Add components</p><label className="flex items-center gap-2 rounded-sm border border-border bg-background px-2"><Search className="size-3.5 text-muted-foreground" /><input aria-label="Search components" placeholder="Search components" className="h-8 min-w-0 flex-1 bg-transparent text-xs outline-none" value={query} onChange={(e) => setQuery(e.target.value)} /></label></div>
        <div className="min-h-0 flex-1 space-y-1 overflow-y-auto p-2">{types.map((kind) => <button key={kind} className={cn("flex w-full items-start gap-2 rounded-sm border p-2 text-left transition-colors hover:border-primary/40 hover:bg-primary/5", placement === kind ? "border-primary bg-primary/10" : "border-transparent")} onClick={() => { editor.setSandboxView("grid"); editor.setTool("select"); setPlacement(kind); }}><Box className="mt-0.5 size-3.5 shrink-0 text-primary" /><span><span className="block text-xs capitalize">{kind.replaceAll("_", " ")}</span><span className="text-[9px] text-muted-foreground">{COMPONENT_SIZES[kind].join(" × ")} m</span></span></button>)}{!types.length && <p className="p-2 text-xs text-muted-foreground">No matching components.</p>}</div>
        <p className="border-t border-border p-3 text-[10px] leading-relaxed text-muted-foreground">Conceptual shapes · metres<br />Click a type, then click the grid.</p>
      </aside>
      <main className="relative min-w-0 flex-1 overflow-hidden" aria-label="Layout scene">
        {editor.sandboxView === "grid" ? <SandboxGrid editor={editor} placement={placement} onPlaced={onPlaced} fit={fit} /> : <CesiumView editor={editor} center={mapCenter} editableModel={doc} selectedComponentIds={editor.selectedIds} onSelectComponent={editor.select} fitRequest={fit.sequence} disableVendor3DTiles localSandbox />}
        {placement && <div className="absolute inset-x-3 top-3 flex items-center justify-between gap-3 rounded-sm border border-primary/30 bg-background/95 px-3 py-2 text-xs shadow-lg"><span>Place <strong className="capitalize text-primary">{placement.replaceAll("_", " ")}</strong> · click the grid · Escape to cancel</span><button aria-label="Cancel placement" onClick={() => setPlacement(null)}><X className="size-4" /></button></div>}
        {!doc.components.length && !placement && <div className="pointer-events-none absolute inset-x-5 top-10 flex justify-center"><div className="max-w-xs rounded-sm border border-white/10 bg-background/90 p-4 text-center shadow-lg"><Grid3X3 className="mx-auto mb-2 size-6 text-primary" /><h2 className="text-sm font-semibold">Build your first layout</h2><p className="mt-2 text-xs leading-relaxed text-muted-foreground">Choose a component from the palette, then click the grid to place it.</p></div></div>}
        <div className="pointer-events-none absolute bottom-3 left-3 rounded-sm border border-white/10 bg-background/85 px-3 py-2 text-[10px] text-muted-foreground">{editor.sandboxView === "grid" ? "1 square = 1 m · bold lines = 10 m · drag to orbit · right drag to pan · scroll to zoom" : "Geographic editor · drag handles or edit values in Properties"}<br />{editor.sandboxView === "grid" && "X east · Y north · Z up · Shift-click for multi-selection"}</div>
      </main>
      <aside className="flex w-64 shrink-0 flex-col overflow-y-auto border-l border-border bg-background-secondary xl:w-72" aria-label="Objects and properties">
        <section className="border-b border-border p-3"><div className="mb-2 flex items-center justify-between"><p className="text-[10px] font-semibold uppercase tracking-widest text-primary">Objects</p><span className="text-[10px] text-muted-foreground">{doc.components.length}</span></div><div className="max-h-48 space-y-1 overflow-y-auto">{doc.components.map((c) => <div key={c.id} className={cn("flex items-center gap-1 rounded-sm px-1.5 py-1", editor.selectedIds.includes(c.id) && "bg-primary/15 ring-1 ring-primary/30")}><button className="min-w-0 flex-1 truncate text-left text-xs" onClick={(e) => editor.select(c.id, e.shiftKey || e.ctrlKey || e.metaKey)}>{c.name}</button><button className="p-1 text-muted-foreground" aria-label={`${c.visible ? "Hide" : "Show"} ${c.name}`} onClick={() => editor.updateComponent(c.id, { visible: !c.visible })}>{c.visible ? <Eye className="size-3" /> : <EyeOff className="size-3" />}</button><button className="p-1 text-muted-foreground" aria-label={`${c.locked ? "Unlock" : "Lock"} ${c.name}`} onClick={() => editor.updateComponent(c.id, { locked: !c.locked })}>{c.locked ? <Lock className="size-3 text-primary" /> : <Unlock className="size-3" />}</button></div>)}{!doc.components.length && <p className="py-2 text-xs text-muted-foreground">Your scene is empty.</p>}</div></section>
        {editor.selected ? <Inspector component={editor.selected} editor={editor} /> : <div className="p-5 text-center text-xs leading-relaxed text-muted-foreground"><MousePointer2 className="mx-auto mb-2 size-5 text-primary" />Select an object to edit its position, dimensions, and color.</div>}
        <section className="mt-auto border-t border-border p-3"><button className="flex w-full items-center justify-between text-[10px] font-semibold uppercase tracking-widest text-muted-foreground" onClick={() => setShowOrigin(!showOrigin)}>Geographic origin<span>{showOrigin ? "−" : "+"}</span></button>{showOrigin && <div className="mt-3 space-y-2"><p className="text-[10px] leading-relaxed text-muted-foreground">Changing the origin relocates the entire layout on the map.</p><div className="grid grid-cols-2 gap-2"><Numeric label="Latitude" value={doc.origin.lat} onChange={(lat) => { if (Math.abs(lat) <= 90) editor.commit({ ...doc, origin: { ...doc.origin, lat } }); }} /><Numeric label="Longitude" value={doc.origin.lng} onChange={(lng) => { if (Math.abs(lng) <= 180) editor.commit({ ...doc, origin: { ...doc.origin, lng } }); }} /></div><Numeric label="Elevation (m)" value={doc.origin.elevation_m} onChange={(elevation_m) => editor.commit({ ...doc, origin: { ...doc.origin, elevation_m } })} /><Numeric label="Heading (°)" value={doc.origin.heading_deg} onChange={(heading_deg) => editor.commit({ ...doc, origin: { ...doc.origin, heading_deg } })} /></div>}</section>
      </aside>
    </div>
    <footer className="flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-border bg-background-secondary px-3 py-2 text-[10px] text-muted-foreground"><span className="font-semibold uppercase tracking-widest text-primary">Conceptual estimates</span><span>Cost {formatCurrency(editor.impact?.total_cost_estimate ?? 0, editor.impact?.currency ?? "INR")}</span><span>Concrete {formatQty(editor.impact?.quantities.concrete_m3 ?? 0, "m³")}</span><span>{editor.selectedIds.length} selected</span><span className={cn("ml-auto", editor.localSaveStatus === "failed" ? "text-amber-300" : "text-primary")} role="status" aria-live="polite">{status}</span><Button className="h-7 text-[10px]" variant="ghost" size="sm" onClick={() => { void editor.save().catch(() => undefined); }}><Save className="size-3" />Save locally</Button></footer>
    {pending && <div className="absolute inset-0 z-50 grid place-items-center bg-black/60 p-4"><div role="dialog" aria-modal="true" aria-labelledby="replace-layout-title" className="w-full max-w-sm rounded-sm border border-border bg-background-secondary p-5 shadow-xl"><h2 id="replace-layout-title" className="text-base font-semibold">{pending.title}</h2><p className="mt-2 text-xs leading-relaxed text-muted-foreground">This replaces your current layout and local save. Download a backup first if you want to keep it.{editor.restoreError && " This also replaces the unreadable saved data."}</p><div className="mt-5 flex justify-end gap-2"><Button variant="outline" size="sm" onClick={() => setPending(null)}>Cancel</Button><Button size="sm" onClick={() => { editor.replaceDocument(pending.payload.document, pending.payload.view, pending.payload.draft); setPlacement(null); setPending(null); requestFit(false); }}>Replace layout</Button></div></div></div>}
  </div>;
}

