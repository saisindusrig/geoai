"use client";

import { useState } from "react";
import { Plus, Save, Building2, Columns3, Route, BrickWall, Layers3, Cable } from "lucide-react";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import type { StructuralElementType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { toastPromise } from "@/lib/toast";

const ELEMENTS: StructuralElementType[] = ["building", "column", "beam", "wall", "slab", "foundation", "road", "bridge", "retaining_wall", "drainage", "pipeline", "utility", "zone", "grid", "construction_phase"];

export default function StructuralPalette({ editor }: { editor: EditableModelEditor }) {
  const [kind, setKind] = useState<StructuralElementType>("column");
  return <section className="space-y-3 border-b border-white/10 bg-gradient-to-br from-primary/[0.045] to-transparent p-4" aria-label="Structural component palette">
    <div className="flex items-center gap-2"><span className="grid size-8 place-items-center rounded-xl bg-primary/10 text-primary"><Plus className="size-4" /></span><div><h2 className="text-sm font-semibold">Build your layout</h2><p className="text-[10px] text-muted-foreground">Conceptual components · metric units</p></div></div>
    <div className="grid grid-cols-3 gap-1.5">{([
      ["building", Building2], ["column", Columns3], ["road", Route], ["wall", BrickWall], ["slab", Layers3], ["pipeline", Cable],
    ] as const).map(([type, Icon]) => <button key={type} aria-pressed={kind === type} onClick={() => setKind(type)} className={`flex flex-col items-center gap-1.5 rounded-xl border px-2 py-2.5 text-[10px] capitalize transition-colors ${kind === type ? "border-primary/40 bg-primary/10 text-primary" : "border-white/10 bg-white/[0.025] text-muted-foreground hover:bg-white/5"}`}><Icon className="size-4" />{type}</button>)}</div>
    <label htmlFor="structural-element" className="sr-only">Component type</label>
    <div className="flex gap-2">
      <select id="structural-element" value={kind} onChange={(event) => setKind(event.target.value as StructuralElementType)} className="min-w-0 flex-1 rounded-sm border border-border bg-background px-2 text-xs">
        {ELEMENTS.map((element) => <option key={element} value={element}>{element.replaceAll("_", " ")}</option>)}
      </select>
      <Button size="sm" onClick={() => editor.addStructuralComponent(kind)} disabled={!editor.document}><Plus className="size-3" />Add</Button>
    </div>
    <p className="text-[10px] text-muted-foreground">Placed at the project origin. Set position and dimensions in Inspect.</p>
    <Button className="w-full" size="sm" disabled={!editor.dirty || editor.saving || !editor.canPersist} onClick={() => {
      void toastPromise(editor.save(), { loading: "Checking and saving layout…", success: "Layout revision saved", error: "Layout could not be saved" }).catch(() => undefined);
    }}><Save className="size-3" />{editor.saving ? "Saving…" : "Validate & save revision"}</Button>
  </section>;
}
