"use client";

import { useMemo, useState, useEffect } from "react";
import { Box, ChevronDown, Eye, EyeOff, Layers3, Lock, ScanEye, Search, Unlock, X } from "lucide-react";

import { Input } from "@/components/ui/input";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import type { EditableModelComponent } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function SceneLayersPanel({ editor }: { editor: EditableModelEditor }) {
  const [query, setQuery] = useState("");
  const [visibilityBeforeIsolation, setVisibilityBeforeIsolation] = useState<Record<string, boolean> | null>(null);
  const [rangeAnchor, setRangeAnchor] = useState<string | null>(null);

  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const components = editor.document?.components;
  useEffect(()=>{const id=editor.selectedIds.at(-1);if(id)document.getElementById(`layer-row-${id}`)?.scrollIntoView?.({block:"nearest"});},[editor.selectedIds]);
  const groups = useMemo(() => {
    const result = new Map<string, EditableModelComponent[]>();
    for (const component of components ?? []) {
      if (!`${component.name} ${component.category}`.toLowerCase().includes(query.trim().toLowerCase())) continue;

      const group = result.get(component.category) ?? [];
      group.push(component);
      result.set(component.category, group);
    }
    return [...result.entries()].map(([category, items]) => [category, items.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }))] as const);
  }, [components, query]);
  if (!editor.document) return null;
  const doc = editor.document;
  const visibleCount = doc.components.filter(component => component.visible).length;
  const changeGroup = (ids: Set<string>, changes: Partial<EditableModelComponent>) => {
    if (!doc.components.some(component => ids.has(component.id) && Object.entries(changes).some(([key, value]) => component[key as keyof EditableModelComponent] !== value))) return;
    editor.commit({ ...doc, components: doc.components.map(component => ids.has(component.id) ? { ...component, ...changes } : component) });
  };
  const showAll = () => changeGroup(new Set(doc.components.map(component => component.id)), { visible: true });
  const isolate = (ids: Set<string>) => {
    if (!visibilityBeforeIsolation) setVisibilityBeforeIsolation(Object.fromEntries(doc.components.map(component => [component.id, component.visible])));
    editor.commit({ ...doc, components: doc.components.map(component => ({ ...component, visible: ids.has(component.id) })) });
  };
  const restoreVisibility = () => {
    if (!visibilityBeforeIsolation) return;
    editor.commit({ ...doc, components: doc.components.map(component => ({ ...component, visible: visibilityBeforeIsolation[component.id] ?? component.visible })) });
    setVisibilityBeforeIsolation(null);
  };
  const selectRow = (id: string, shift: boolean, additive: boolean) => {
    const ordered = groups.flatMap(([, items]) => items.map(item => item.id));
    if (shift && rangeAnchor && ordered.includes(rangeAnchor)) {
      const start = ordered.indexOf(rangeAnchor), end = ordered.indexOf(id);
      editor.selectMany([...editor.selectedIds, ...ordered.slice(Math.min(start, end), Math.max(start, end) + 1)]);
    } else { editor.select(id, additive); setRangeAnchor(id); }
  };

  return <div className="flex min-h-full flex-col" aria-label="Scene layer explorer">
    <div className="sticky top-0 z-10 space-y-1.5 border-b border-white/10 bg-[#111a18]/95 px-3 py-2 backdrop-blur-xl">
      <div className="flex items-center justify-between gap-2"><div><h3 className="text-xs font-semibold">Scene layers</h3><p className="mt-0.5 text-[9px] text-muted-foreground">{doc.components.length} objects · {visibleCount} visible · {doc.components.length - visibleCount} hidden</p></div><span className={cn("rounded-full px-1.5 py-0.5 text-[9px]", editor.dirty ? "bg-amber-400/10 text-amber-200" : "bg-primary/10 text-primary")}>{editor.dirty ? "Unsaved" : "Saved"}</span></div>
      <div className="relative"><Search className="pointer-events-none absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" /><Input aria-label="Search scene components" placeholder="Find an object or layer…" value={query} onChange={event => setQuery(event.target.value)} className="h-7 border-white/10 bg-black/20 pl-9 pr-8 text-xs" />{query && <button aria-label="Clear layer search" onClick={() => setQuery("")} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground"><X className="size-3" /></button>}</div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px]"><button className="flex items-center gap-1 text-muted-foreground hover:text-primary" onClick={showAll}><Eye className="size-3" />Show all</button><button className="text-muted-foreground hover:text-primary" onClick={() => setExpanded(Object.fromEntries(groups.map(([category]) => [category, true])))}>Expand</button><button className="text-muted-foreground hover:text-primary" onClick={() => setExpanded(Object.fromEntries(groups.map(([category]) => [category, false])))}>Collapse all</button><details className="relative ml-auto"><summary className="cursor-pointer text-primary">Actions</summary><div className="absolute right-0 top-full z-20 mt-2 w-44 border border-white/15 bg-[#111a18] p-1 shadow-xl">{([
        ["Select matching", () => editor.selectMany(groups.flatMap(([, items]) => items.map(item => item.id)))],
        ["Clear selection", () => editor.selectMany([])],
        ["Hide selected", () => changeGroup(new Set(editor.selectedIds), { visible: false })],
        ["Lock selected", () => changeGroup(new Set(editor.selectedIds), { locked: true })],
        ["Unlock selected", () => changeGroup(new Set(editor.selectedIds), { locked: false })],
        ["Isolate selected", () => isolate(new Set(editor.selectedIds))],
      ] as const).map(([label, action]) => <button key={label} disabled={label.endsWith("selected") && !editor.selectedIds.length} className="block w-full px-2 py-2 text-left hover:bg-white/5 disabled:opacity-35" onClick={event => { action(); event.currentTarget.closest("details")?.removeAttribute("open"); }}>{label}</button>)}</div></details></div>
      {visibilityBeforeIsolation && <button className="text-[10px] text-primary" onClick={restoreVisibility}>Exit isolation · restore visibility</button>}
      {doc.components.some(c => c.category === "room") && <div className="flex gap-3 text-[10px]">
        <button className="text-primary" onClick={() => isolate(new Set(doc.components.filter(c => ["room", "wall", "door", "window", "slab"].includes(c.category)).map(c => c.id)))}>Architecture</button>
        <button className="text-primary" onClick={() => isolate(new Set(doc.components.filter(c => ["column", "beam", "slab", "foundation"].includes(c.category)).map(c => c.id)))}>Structural frame</button>
      </div>}
      {!!editor.selectedIds.length && <div className="flex items-center justify-between text-[10px] text-primary"><span>{editor.selectedIds.length} selected · Shift for range</span><button onClick={() => window.dispatchEvent(new CustomEvent("geoai:locate-component", { detail: editor.selectedIds[0] }))}>Locate</button></div>}
    </div>
    <div className="flex-1 space-y-2 p-3">
      {groups.length === 0 && <div className="flex flex-col items-center gap-2 py-8 text-center"><Search className="size-6 text-muted-foreground" /><p className="text-xs text-muted-foreground">No matching components.</p><button className="text-xs text-primary" onClick={() => setQuery("")}>Clear search</button></div>}
      {groups.map(([category, items]) => {
        const isOpen = query.trim().length > 0 || (expanded[category] ?? (items.some(item=>editor.selectedIds.includes(item.id)) || items.length <= 6));
        const ids = new Set(items.map(component => component.id));
        const allHidden = items.every(component => !component.visible);
        const allLocked = items.every(component => component.locked);
        return <section key={category} className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.02]" aria-label={`${category} layer`}>
          <div className="flex items-center gap-1 px-2 py-2">
            <button className="flex min-w-0 flex-1 items-center gap-2 text-left" aria-label={`${isOpen ? "Collapse" : "Expand"} ${category}`} aria-expanded={isOpen} onClick={() => setExpanded(previous => ({ ...previous, [category]: !isOpen }))}><ChevronDown className={cn("size-3.5 shrink-0 text-muted-foreground transition-transform", !isOpen && "-rotate-90")} /><span className="grid size-7 shrink-0 place-items-center rounded-lg bg-white/5"><Layers3 className="size-3.5" style={{ color: items[0]?.material.color }} /></span><span className="truncate text-xs font-semibold capitalize">{category.replaceAll("_", " ")}</span><span className="ml-auto rounded-md bg-white/5 px-1.5 py-0.5 text-[9px] text-muted-foreground">{items.length}</span></button>
            <button aria-label={`${allHidden ? "Show" : "Hide"} ${category} layer`} title={`${allHidden ? "Show" : "Hide"} layer`} className="rounded-md p-1.5 text-muted-foreground hover:bg-white/5 hover:text-primary" onClick={() => changeGroup(ids, { visible: allHidden })}>{allHidden ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}</button>
            <button aria-label={`${allLocked ? "Unlock" : "Lock"} ${category} layer`} title={`${allLocked ? "Unlock" : "Lock"} layer`} className="rounded-md p-1.5 text-muted-foreground hover:bg-white/5 hover:text-primary" onClick={() => changeGroup(ids, { locked: !allLocked })}>{allLocked ? <Lock className="size-3.5 text-amber-200" /> : <Unlock className="size-3.5" />}</button>
            <button aria-label={`Isolate ${category} layer`} title="Show only this layer · restore from header" className="rounded-md p-1.5 text-muted-foreground hover:bg-white/5 hover:text-primary" onClick={() => isolate(ids)}><ScanEye className="size-3.5" /></button>
          </div>
          {isOpen && <div className="space-y-0.5 border-t border-white/5 p-1.5">{items.map(component => <div id={`layer-row-${component.id}`} key={component.id} className={cn("flex items-center gap-1 rounded-lg px-1.5 py-1", editor.selectedIds.includes(component.id) ? "bg-primary/10 ring-1 ring-inset ring-primary/30" : "hover:bg-white/[0.04]", !component.visible && "opacity-55")}>
            <button className="flex min-w-0 flex-1 items-center gap-2 py-1.5 text-left text-[11px]" aria-pressed={editor.selectedIds.includes(component.id)} onDoubleClick={() => window.dispatchEvent(new CustomEvent("geoai:locate-component", { detail: component.id }))} onClick={event => selectRow(component.id, event.shiftKey, event.ctrlKey || event.metaKey)} title="Select · Ctrl to add · Shift for range · double-click to locate"><Box className="size-3.5 shrink-0 text-muted-foreground" /><span className="truncate">{component.name}</span></button>
            <button aria-label={`${component.visible ? "Hide" : "Show"} ${component.name}`} title={component.visible ? "Hide object" : "Show object"} className="rounded-md p-1.5 text-muted-foreground hover:text-primary" onClick={() => editor.updateComponent(component.id, { visible: !component.visible })}>{component.visible ? <Eye className="size-3.5" /> : <EyeOff className="size-3.5" />}</button>
            <button aria-label={`${component.locked ? "Unlock" : "Lock"} ${component.name}`} title={component.locked ? "Unlock object" : "Lock object"} className="rounded-md p-1.5 text-muted-foreground hover:text-primary" onClick={() => editor.updateComponent(component.id, { locked: !component.locked })}>{component.locked ? <Lock className="size-3.5 text-amber-200" /> : <Unlock className="size-3.5" />}</button>
          </div>)}</div>}
        </section>;
      })}
    </div>
  </div>;
}



