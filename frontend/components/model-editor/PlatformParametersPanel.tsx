"use client";
import { useState } from "react";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";
import { previewPlatform, readPlatform, type PlatformParameters } from "@/lib/parametric-platform";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const fields: [keyof PlatformParameters,string][] = [["length","Platform length"],["width","Platform width"],["height","Deck height"],["slabThickness","Slab thickness"],["beamWidth","Beam width"],["beamDepth","Beam depth"],["columnWidth","Column width"],["columnDepth","Column depth"]];
export default function PlatformParametersPanel({editor}:{editor:EditableModelEditor}) {
  const initial=editor.document && readPlatform(editor.document);
  if(!initial) return null;
  return <PlatformForm key={JSON.stringify(initial)} editor={editor} initial={initial}/>;
}
function PlatformForm({editor,initial}:{editor:EditableModelEditor;initial:PlatformParameters}) {
  const [draft,setDraft]=useState(()=>Object.fromEntries(Object.entries(initial).map(([k,v])=>[k,String(Number(v.toFixed(6)))])));
  const [error,setError]=useState<string|null>(null);
  const cancel=()=>editor.setPlatformPreview(null);
  return <section aria-label="Parametric maintenance platform" className="space-y-3 border-b border-border p-3">
    <div><h3 className="text-sm font-medium">Maintenance platform</h3><p className="mt-1 text-[11px] text-muted-foreground">Parametric assembly · 1 slab, 4 beams, 4 columns</p></div>
    <p className="text-[11px] text-amber-200">Conceptual / unverified member sizes. Geometry checks only; structural adequacy, loads and foundations are unverified.</p>
    <div className="grid grid-cols-2 gap-2">{fields.map(([key,label])=><label key={key} className="space-y-1 text-[10px] text-muted-foreground"><span>{label} · m</span><Input aria-label={`${label} · m`} className="h-8 px-2 text-xs" inputMode="decimal" value={draft[key]} onChange={e=>{cancel();setError(null);setDraft({...draft,[key]:e.target.value});}} /></label>)}</div>
    <p className="text-[10px] text-muted-foreground">Height is measured from the local column-base plane to the deck top. Preview realigns all nine members around the deck centre.</p>
    {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
    {editor.platformPreview && !editor.platformPreview.label && <div role="status" className="space-y-1 rounded border border-primary/30 p-2 text-[11px]"><p>Preview only · model has not changed</p><p>Positive sizes, clear spans, slab–beam and beam–column contact verified geometrically.</p><p>Platform members and attached assemblies will update in one undoable edit.</p></div>}
    <div className="flex gap-2"><Button size="sm" variant="outline" onClick={()=>{try {if(!editor.document) return; const p=Object.fromEntries(Object.entries(draft).map(([k,v])=>[k,v.trim()?Number(v):NaN])) as PlatformParameters;const candidate=previewPlatform(editor.document,p); editor.setComparison(null);editor.setPlatformPreview({source:editor.document,document:candidate});setError(null);}catch(e){cancel();setError((e as Error).message);}}}>Preview platform</Button>
    {editor.platformPreview && !editor.platformPreview.label && <><Button size="sm" onClick={()=>{if(editor.platformPreview)editor.commit(editor.platformPreview.document);cancel();}}>Apply platform</Button><Button size="sm" variant="ghost" onClick={cancel}>Cancel</Button></>}</div>
  </section>;
}
