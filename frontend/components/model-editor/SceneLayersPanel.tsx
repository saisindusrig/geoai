"use client";

import { useMemo, useState, useEffect } from "react";
import { Box, ChevronDown, Eye, EyeOff, Folder, FolderOpen, Layers3, Lock, ScanEye, Search, Unlock, X } from "lucide-react";

import { Input } from "@/components/ui/input";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import type { EditableModelComponent } from "@/lib/types";
import {componentDisplayName} from "@/lib/component-presentation";
import {componentOverlaps} from "@/lib/component-overlaps";
import { cn } from "@/lib/utils";

export default function SceneLayersPanel({ editor }: { editor: EditableModelEditor }) {
  const [query, setQuery] = useState("");
  const [filter,setFilter]=useState("all");
  const [visibilityBeforeIsolation, setVisibilityBeforeIsolation] = useState<Record<string, boolean> | null>(null);
  const [rangeAnchor, setRangeAnchor] = useState<string | null>(null);

  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({});
  const components = editor.document?.components;
  const selectedId = editor.selectedIds.at(-1) ?? null;
  const [lastExpandedSelection, setLastExpandedSelection] = useState<string | null>(null);
  if (selectedId !== lastExpandedSelection) {
    setLastExpandedSelection(selectedId);
    const selected = components?.find(component => component.id === selectedId);
    if (selected) {
      setExpanded(previous => ({ ...previous, [selected.category]: true }));
      setExpandedFolders(previous => ({ ...previous, Architecture: true, "Structural frame": true, "Site & systems": true }));
    }
  }
  useEffect(() => {
    if (selectedId) document.getElementById(`layer-row-${selectedId}`)?.scrollIntoView?.({ block: "nearest" });
  }, [selectedId]);
  const overlaps=useMemo(()=>componentOverlaps(components??[]),[components]);
  const groups = useMemo(() => {
    const result = new Map<string, EditableModelComponent[]>();
    for (const component of components ?? []) {
      if(filter==='selected'&&!editor.selectedIds.includes(component.id)||filter==='hidden'&&component.visible||filter==='visible'&&!component.visible||filter==='locked'&&!component.locked)continue;
      if (!`${componentDisplayName(component)} ${componentDisplayName(component)} ${component.id} ${component.category} ${JSON.stringify(component.metadata?.drawing_cad??{})}`.toLowerCase().includes(query.trim().toLowerCase())) continue;

      const group = result.get(component.category) ?? [];
      group.push(component);
      result.set(component.category, group);
    }
    return [...result.entries()].map(([category, items]) => [category, items.sort((a, b) => componentDisplayName(a).localeCompare(componentDisplayName(b), undefined, { numeric: true }))] as const);
  }, [components, query,filter,editor.selectedIds]);
  const folders = useMemo(() => {
    const result = new Map<string, (typeof groups)[number][]>();
    for (const group of groups) {
      const category = group[0].toLowerCase();
      const folder = ["room", "wall", "door", "window", "slab", "roof", "stair", "balcony"].some(value => category.includes(value))
        ? "Architecture"
        : ["abutment", "deck", "pier", "column", "beam", "foundation", "footing", "girder", "brac", "base_plate", "connection"].some(value => category.includes(value))
          ? "Structural frame"
          : "Site & systems";
      result.set(folder, [...(result.get(folder) ?? []), group]);
    }
    return [...result.entries()];
  }, [groups]);
  useEffect(()=>{const listener=(event:Event)=>{const action=(event as CustomEvent<string>).detail;const doc=editor.document;if(!doc)return;
    if(action==='restore'&&visibilityBeforeIsolation){editor.commit({...doc,components:doc.components.map(c=>({...c,visible:visibilityBeforeIsolation[c.id]??c.visible}))});setVisibilityBeforeIsolation(null);}
    if(action==='hide'){if(!visibilityBeforeIsolation)setVisibilityBeforeIsolation(Object.fromEntries(doc.components.map(c=>[c.id,c.visible])));editor.commit({...doc,components:doc.components.map(c=>editor.selectedIds.includes(c.id)?{...c,visible:false}:c)});}
    if(action==='isolate'){if(!visibilityBeforeIsolation)setVisibilityBeforeIsolation(Object.fromEntries(doc.components.map(c=>[c.id,c.visible])));editor.commit({...doc,components:doc.components.map(c=>({...c,visible:editor.selectedIds.includes(c.id)}))});}
  };window.addEventListener('geoai:layer-action',listener);return()=>window.removeEventListener('geoai:layer-action',listener);},[editor,visibilityBeforeIsolation]);
  if (!editor.document) return null;
  const doc = editor.document;
  const visibleCount = doc.components.filter(component => component.visible).length;
  const changeGroup = (ids: Set<string>, changes: Partial<EditableModelComponent>) => {
    if (!doc.components.some(component => ids.has(component.id) && Object.entries(changes).some(([key, value]) => component[key as keyof EditableModelComponent] !== value))) return;
    if(changes.visible!==undefined&&!visibilityBeforeIsolation)setVisibilityBeforeIsolation(Object.fromEntries(doc.components.map(c=>[c.id,c.visible])));
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
      <label className="flex items-center gap-2 text-[10px]">Filter<select aria-label="Component filter" className="min-w-0 flex-1 rounded border border-border bg-background p-1" value={filter} onChange={e=>setFilter(e.target.value)}>{['all','selected','visible','hidden','locked'].map(v=><option key={v} value={v}>{v[0].toUpperCase()+v.slice(1)}</option>)}</select></label>
      {!!overlaps.length&&<details className="text-[10px] text-amber-200"><summary>{overlaps.length} envelope overlaps · review</summary><p className="py-1">Bounding envelopes may overlap intentionally. This is not a solid-clash test or a structural connection. No geometry was changed.</p><div className="max-h-40 overflow-auto">{overlaps.map((pair,i)=><button key={i} className="block py-1 text-left" onClick={()=>editor.selectMany([pair.a,pair.b])}>{pair.kind}: {componentDisplayName(doc.components.find(c=>c.id===pair.a)!)} / {componentDisplayName(doc.components.find(c=>c.id===pair.b)!)}</button>)}</div></details>}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px]"><button className="flex items-center gap-1 text-muted-foreground hover:text-primary" onClick={showAll}><Eye className="size-3" />Show all</button><button className="text-muted-foreground hover:text-primary" onClick={() => { setExpanded(Object.fromEntries(groups.map(([category]) => [category, true]))); setExpandedFolders(Object.fromEntries(folders.map(([folder]) => [folder, true]))); }}>Expand</button><button className="text-muted-foreground hover:text-primary" onClick={() => { setExpanded({}); setExpandedFolders({}); }}>Collapse all</button><details className="relative ml-auto"><summary className="cursor-pointer text-primary">Actions</summary><div className="absolute right-0 top-full z-20 mt-2 w-44 border border-white/15 bg-[#111a18] p-1 shadow-xl">{([
        ["Select matching", () => editor.selectMany(groups.flatMap(([, items]) => items.map(item => item.id)))],
        ["Clear selection", () => editor.selectMany([])],
        ["Show selected", () => changeGroup(new Set(editor.selectedIds), { visible: true })],
        ["Inspect selected", () => window.dispatchEvent(new Event("geoai:selection-inspect"))],
        ["Focus selected", () => window.dispatchEvent(new Event("geoai:fit-selection"))],
        ["Hide selected", () => changeGroup(new Set(editor.selectedIds), { visible: false })],
        ["Lock selected", () => changeGroup(new Set(editor.selectedIds), { locked: true })],
        ["Unlock selected", () => changeGroup(new Set(editor.selectedIds), { locked: false })],
        ["Isolate selected", () => isolate(new Set(editor.selectedIds))],
      ] as const).map(([label, action]) => <button key={label} disabled={label.endsWith("selected") && !editor.selectedIds.length} className="block w-full px-2 py-2 text-left hover:bg-white/5 disabled:opacity-35" onClick={event => { action(); event.currentTarget.closest("details")?.removeAttribute("open"); }}>{label}</button>)}</div></details></div>
      {visibilityBeforeIsolation && <button className="text-[10px] text-primary" onClick={restoreVisibility}>Restore previous visibility</button>}
      {doc.components.some(c => c.category === "room") && <div className="flex gap-3 text-[10px]">
        <button className="text-primary" onClick={() => isolate(new Set(doc.components.filter(c => ["room", "wall", "door", "window", "slab"].includes(c.category)).map(c => c.id)))}>Architecture</button>
        <button className="text-primary" onClick={() => isolate(new Set(doc.components.filter(c => ["column", "beam", "slab", "foundation"].includes(c.category)).map(c => c.id)))}>Structural frame</button>
      </div>}
      {editor.selectedIds.some(id=>!groups.some(([,items])=>items.some(c=>c.id===id)))&&<button className="text-[10px] text-primary" onClick={()=>{setQuery('');setFilter('selected');}}>Reveal selection · outside current filter</button>}
      {!!editor.selectedIds.length && <div className="flex items-center justify-between text-[10px] text-primary"><span>{editor.selectedIds.length} selected · Shift for range</span><button onClick={() => window.dispatchEvent(new CustomEvent("geoai:locate-component", { detail: editor.selectedIds[0] }))}>Locate</button></div>}
    </div>
    <div className="flex-1 space-y-2 p-3">
      {groups.length === 0 && <div className="flex flex-col items-center gap-2 py-8 text-center"><Search className="size-6 text-muted-foreground" /><p className="text-xs text-muted-foreground">No matching components.</p><button className="text-xs text-primary" onClick={() => setQuery("")}>Clear search</button></div>}
      {folders.map(([folder, folderGroups]) => {
        const isOpen = query.trim().length > 0 || (expandedFolders[folder] ?? true);
        const folderIds = new Set(folderGroups.flatMap(([, items]) => items.map(item => item.id)));
        const folderHidden = folderGroups.flatMap(([, items]) => items).every(item => !item.visible);
        return <section key={folder} aria-label={`${folder} folder`} className="overflow-hidden rounded-xl border border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-1 border-b border-white/5 bg-white/[0.025] px-2 py-1.5">
            <button className="flex min-w-0 flex-1 items-center gap-2 text-left" aria-label={`${isOpen ? "Collapse" : "Expand"} ${folder} folder`} aria-expanded={isOpen} onClick={() => setExpandedFolders(previous => ({ ...previous, [folder]: !isOpen }))}>
              <ChevronDown className={cn("size-3.5 shrink-0 text-muted-foreground transition-transform", !isOpen && "-rotate-90")} />
              {isOpen ? <FolderOpen className="size-4 shrink-0 text-primary" /> : <Folder className="size-4 shrink-0 text-primary" />}
              <span className="truncate text-[11px] font-semibold">{folder}</span>
              <span className="ml-auto rounded-md bg-white/5 px-1.5 py-0.5 text-[9px] text-muted-foreground">{folderIds.size}</span>
            </button>
            <button aria-label={`${folderHidden ? "Show" : "Hide"} ${folder}`} title={`${folderHidden ? "Show" : "Hide"} folder`} className="rounded-md p-1.5 text-muted-foreground hover:bg-white/5 hover:text-primary" onClick={() => changeGroup(folderIds, { visible: folderHidden })}>{folderHidden ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}</button>
          </div>
          {isOpen && <div className="space-y-1.5 p-1.5">{folderGroups.map(([category, items]) => {
            const categoryOpen = query.trim().length > 0 || (expanded[category] ?? (items.some(item => editor.selectedIds.includes(item.id)) || items.length <= 6));
            const ids = new Set(items.map(component => component.id));
            const allHidden = items.every(component => !component.visible);
            const allLocked = items.every(component => component.locked);
            return <section key={category} className="overflow-hidden rounded-lg border border-white/[0.07]" aria-label={`${category} layer`}>
              <div className="flex items-center gap-1 px-1.5 py-1">
                <button className="flex min-w-0 flex-1 items-center gap-1.5 text-left" aria-label={`${categoryOpen ? "Collapse" : "Expand"} ${category}`} aria-expanded={categoryOpen} onClick={() => setExpanded(previous => ({ ...previous, [category]: !categoryOpen }))}><ChevronDown className={cn("size-3 shrink-0 text-muted-foreground transition-transform", !categoryOpen && "-rotate-90")} /><span className="grid size-5 shrink-0 place-items-center rounded bg-white/5"><Layers3 className="size-3" style={{ color: items[0]?.material.color }} /></span><span className="truncate text-[10px] font-medium capitalize">{category.replaceAll("_", " ")}</span><span className="ml-auto rounded bg-white/5 px-1 py-0.5 text-[9px] text-muted-foreground">{items.length}</span></button>
                <button aria-label={`${allHidden ? "Show" : "Hide"} ${category} layer`} title={`${allHidden ? "Show" : "Hide"} layer`} className="rounded p-1 text-muted-foreground hover:bg-white/5 hover:text-primary" onClick={() => changeGroup(ids, { visible: allHidden })}>{allHidden ? <EyeOff className="size-3" /> : <Eye className="size-3" />}</button>
                <button aria-label={`${allLocked ? "Unlock" : "Lock"} ${category} layer`} title={`${allLocked ? "Unlock" : "Lock"} layer`} className="rounded p-1 text-muted-foreground hover:bg-white/5 hover:text-primary" onClick={() => changeGroup(ids, { locked: !allLocked })}>{allLocked ? <Lock className="size-3 text-amber-200" /> : <Unlock className="size-3" />}</button>
                <button aria-label={`Isolate ${category} layer`} title="Show only this layer · restore from header" className="rounded p-1 text-muted-foreground hover:bg-white/5 hover:text-primary" onClick={() => isolate(ids)}><ScanEye className="size-3" /></button>
              </div>
              {categoryOpen && <div className="space-y-0.5 border-t border-white/5 p-1">{items.map(component => <div id={`layer-row-${component.id}`} key={component.id} className={cn("flex items-center gap-1 rounded-lg px-1.5 py-1", editor.selectedIds.includes(component.id) ? "bg-primary/10 ring-1 ring-inset ring-primary/30" : "hover:bg-white/[0.04]", !component.visible && "opacity-55")}>
                <button className="flex min-w-0 flex-1 items-center gap-2 py-1.5 text-left text-[11px]" aria-pressed={editor.selectedIds.includes(component.id)} onDoubleClick={() => window.dispatchEvent(new CustomEvent("geoai:locate-component", { detail: component.id }))} onClick={event => selectRow(component.id, event.shiftKey, event.ctrlKey || event.metaKey)} title={`${componentDisplayName(component)} · ${component.id} · Ctrl to add · Shift for range · double-click to locate`}><Box className="size-3.5 shrink-0 text-muted-foreground" /><span className="truncate">{componentDisplayName(component)}</span></button>
                <button aria-label={`${component.visible ? "Hide" : "Show"} ${componentDisplayName(component)}`} title={component.visible ? "Hide object" : "Show object"} className="rounded-md p-1.5 text-muted-foreground hover:text-primary" onClick={() => changeGroup(new Set([component.id]), { visible: !component.visible })}>{component.visible ? <Eye className="size-3.5" /> : <EyeOff className="size-3.5" />}</button>
                <button aria-label={`${component.locked ? "Unlock" : "Lock"} ${componentDisplayName(component)}`} title={component.locked ? "Unlock object" : "Lock object"} className="rounded-md p-1.5 text-muted-foreground hover:text-primary" onClick={() => editor.updateComponent(component.id, { locked: !component.locked })}>{component.locked ? <Lock className="size-3.5 text-amber-200" /> : <Unlock className="size-3.5" />}</button>
              </div>)}</div>}
            </section>;
          })}</div>}
        </section>;
      })}
    </div>
  </div>;
}



