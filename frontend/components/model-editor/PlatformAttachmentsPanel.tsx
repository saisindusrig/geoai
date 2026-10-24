"use client";
import {useState} from "react";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import type {EditableModelEditor} from "@/hooks/useEditableModelEditor";
import {attachments,attachmentOf,ATTACHMENT_DEFAULTS,previewAttachment,validateAttachments,type Attachment,type AttachmentKind} from "@/lib/platform-attachments";
import {platformMembers,readPlatform} from "@/lib/parametric-platform";

const labels:Record<AttachmentKind,string>={foundation:"Foundation",base_plate:"Base plate",brace:"Bracing",stairs:"Stairs",connection:"Connection placeholder"};
const fields:Record<string,string>={width:"Width",depth:"Depth",thickness:"Thickness",radius:"Brace radius",going:"Tread going",maxRiser:"Maximum riser",treadThickness:"Tread thickness",stringerRadius:"Stringer radius"};
export default function PlatformAttachmentsPanel({editor}:{editor:EditableModelEditor}) {
  if(!editor.document || !platformMembers(editor.document))return null;
  return <AttachmentControls key={`${editor.document.project_id}:${editor.document.scenario_id}`} editor={editor}/>;
}
function AttachmentControls({editor}:{editor:EditableModelEditor}) {
  const [active,setActive]=useState<string|null>(null),[kind,setKind]=useState<AttachmentKind>("foundation");
  const [refs,setRefs]=useState<string[]>(["industrial-platform-5x3:column-sw"]);
  const [draft,setDraft]=useState<Record<string,string>>(()=>Object.fromEntries(Object.entries(ATTACHMENT_DEFAULTS.foundation).map(([k,v])=>[k,String(v)])));
  const [error,setError]=useState<string|null>(null);
  const doc=editor.document!;
  let items:Attachment[]=[];try{items=attachments(doc);}catch(e){return <p role="alert" className="p-3 text-xs text-destructive">{(e as Error).message}</p>;}
  const validation=validateAttachments(doc);
  const platform=readPlatform(doc), risers=platform ? Math.ceil(platform.height/Number(draft.maxRiser)) : NaN;
  const flight=kind==="stairs" && platform && Number.isFinite(risers) && risers>=2 && risers<=200 && Number(draft.going)>0 ? `${risers} equal risers · rise ${Number((platform.height/risers).toFixed(3))} m · run ${Number((risers*Number(draft.going)).toFixed(3))} m` : null;
  const cancel=()=>editor.setPlatformPreview(null);
  const choose=(a:Attachment)=>{cancel();setError(null);setActive(a.id);setKind(a.kind);setRefs(a.refs);setDraft(Object.fromEntries(Object.entries(a.parameters).map(([k,v])=>[k,String(Number(v.toFixed(6)))])));const part=doc.components.find(c=>attachmentOf(c)===a.id);if(part)editor.select(part.id);};
  const defaults=(value:AttachmentKind)=>{cancel();setError(null);setActive(null);setKind(value);setDraft(Object.fromEntries(Object.entries(ATTACHMENT_DEFAULTS[value]).map(([k,v])=>[k,String(v)])));setRefs(value==="stairs"?["industrial-platform-5x3:platform-deck"]:value==="brace"?["industrial-platform-5x3:column-sw","industrial-platform-5x3:column-nw"]:value==="connection"?["industrial-platform-5x3:column-sw","industrial-platform-5x3:beam-south"]:["industrial-platform-5x3:column-sw"]);};
  const preview=(remove=false)=>{try {
    if(remove&&!active)throw new Error("Select an attached assembly to delete.");
    const id=active??crypto.randomUUID();const p=Object.fromEntries(Object.entries(draft).map(([k,v])=>[k,v.trim()?Number(v):NaN]));
    const candidate=previewAttachment(doc,remove?null:{id,kind,refs,parameters:p},remove?id:undefined);
    editor.setComparison(null);editor.setEditError(null);editor.setPlatformPreview({source:doc,document:candidate,label:remove?"Delete attached assembly":active?"Edit attached assembly":"Add attached assembly"});setError(null);
  }catch(e){cancel();setError((e as Error).message);}};
  return <section aria-label="Attached platform components" className="space-y-3 border-b border-border p-3">
    <div className="flex items-center justify-between gap-2"><h3 className="text-sm font-medium">Attached components</h3><Button size="sm" variant="ghost" className="h-7 px-2 text-[10px]" onClick={()=>window.dispatchEvent(new CustomEvent("geoai:frame-platform-assembly"))}>Frame assembly</Button></div>
    <p className="text-[11px] text-muted-foreground">Real solids linked to member references. Foundation and plate dimensions are assumed; bracing uses solid round members; stairs use discrete treads and two round stringers. Connections are solid joint envelopes with no bolts, welds or strength verification.</p>
    <p className="text-[11px] text-amber-200">Conceptual / unverified. Column-base plane is a local reference, not surveyed ground. Supports extend below that plane. No soil, anchorage, stair safety or code checks.</p>
    <details open={items.length===0} className="space-y-2"><summary className="cursor-pointer text-xs">{items.length} attached assemblies · select / edit</summary><div className="mt-2 max-h-40 space-y-1 overflow-y-auto">{items.map(a=><Button key={a.id} size="sm" variant={active===a.id?"secondary":"ghost"} className="h-auto w-full justify-start whitespace-normal py-1 text-left text-[11px]" aria-label={`Edit ${labels[a.kind]} ${a.id}`} onClick={()=>choose(a)}>{labels[a.kind]} · {a.refs.map(r=>r.split(":").at(-1)).join(" → ")}</Button>)}</div></details>
    {attachmentOf(editor.selected) && <Button size="sm" variant="outline" onClick={()=>{const a=items.find(a=>a.id===attachmentOf(editor.selected));if(a)choose(a);}}>Edit selected attachment</Button>}
    <label className="block space-y-1 text-[10px]">Component type<select aria-label="Attached component type" className="h-8 w-full border border-border bg-background px-2 text-xs" value={kind} onChange={e=>defaults(e.target.value as AttachmentKind)}>{Object.entries(labels).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
    {active && <p className="text-[10px] text-muted-foreground">Editing selected assembly · <button className="text-primary" onClick={()=>defaults(kind)}>New assembly</button></p>}
    {refs.map((ref,i)=><label key={i} className="block space-y-1 text-[10px]">{kind==="stairs"?"Deck reference":kind==="brace"?i?"Upper column reference":"Lower column reference":i?"Beam reference":"Column reference"}<select aria-label={`Attachment reference ${i+1}`} className="h-8 w-full border border-border bg-background px-2 text-xs" value={ref} onChange={e=>{cancel();setError(null);setRefs(refs.map((v,n)=>n===i?e.target.value:v));}}>{doc.components.filter(c=>c.id.startsWith("industrial-platform-5x3:") && (kind==="stairs"?c.category==="slab":kind==="connection"&&i===1?c.category==="beam":c.category==="column")).map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>)}
    <div className="grid grid-cols-2 gap-2">{Object.keys(ATTACHMENT_DEFAULTS[kind]).map(k=><label key={k} className="space-y-1 text-[10px] text-muted-foreground"><span>{fields[k]} · m</span><Input aria-label={`Attachment ${fields[k]} · m`} className="h-8 px-2 text-xs" inputMode="decimal" value={draft[k]??""} onChange={e=>{cancel();setError(null);setDraft({...draft,[k]:e.target.value});}}/></label>)}</div>
    {kind==="stairs"&&<p className="text-[10px] text-muted-foreground">South-edge flight. Rise follows deck height. Riser count rounds up from the maximum riser; all risers are equal. Going controls the total run. Treads and stringers are regenerated together.</p>}
    {flight && <p aria-label="Stair draft dimensions" className="text-[11px] text-primary">Draft: {flight}</p>}
    {error&&<p role="alert" className="text-xs text-destructive">{error}</p>}
    {validation.length>0&&<p role="alert" className="text-xs text-destructive">{validation.join(" ")}</p>}
    <div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={()=>preview()}>{active?"Preview attachment edit":"Preview addition"}</Button>{active&&<Button size="sm" variant="outline" onClick={()=>preview(true)}>Preview deletion</Button>}</div>
    {editor.platformPreview?.label&&<div role="status" className="space-y-2 rounded border border-primary/30 p-2 text-[11px]"><p>{editor.platformPreview.label} · preview only, not applied</p><p>Positive dimensions, references and geometric attachment checks passed. No structural analysis.</p><div className="flex gap-2"><Button size="sm" onClick={()=>{const p=editor.platformPreview;if(p){editor.commit(p.document);const id=attachmentOf(p.document.components.find(c=>!doc.components.some(old=>old.id===c.id)));if(id){setActive(id);const part=p.document.components.find(c=>attachmentOf(c)===id);if(part)editor.select(part.id);}if(p.label === "Delete attached assembly")setActive(null);}cancel();}}>Apply attachment</Button><Button size="sm" variant="ghost" onClick={cancel}>Cancel attachment preview</Button></div></div>}
  </section>;
}
