import type { EditableModelComponent, EditableModelDocument, EditableGeometry } from "./types";

export type AttachmentKind = "foundation" | "base_plate" | "brace" | "stairs" | "connection";
export type Attachment = { id: string; kind: AttachmentKind; refs: string[]; parameters: Record<string, number> };
export const ATTACHMENT_DEFAULTS: Record<AttachmentKind, Record<string, number>> = {
  foundation: { width: 1.2, depth: 1.2, thickness: 0.45 },
  base_plate: { width: 0.65, depth: 0.65, thickness: 0.025 },
  brace: { radius: 0.04 },
  stairs: { width: 1, going: 0.28, maxRiser: 0.18, treadThickness: 0.04, stringerRadius: 0.05 },
  connection: { width: 0.5, depth: 0.5, thickness: 0.12 },
};
const prefix = "industrial-platform-5x3:";
type Vec = [number, number, number];
export function attachments(doc: EditableModelDocument): Attachment[] {
  const value = doc.generator_parameters.platform_attachments;
  if (value === undefined) return [];
  if (!value || typeof value !== "object" || !("version" in value) || value.version !== 1 || !("items" in value) || !Array.isArray(value.items)) throw new Error("Unsupported attachment parameter data.");
  return value.items as Attachment[];
}
export function attachmentOf(c: EditableModelComponent | null | undefined): string | null {
  return typeof c?.metadata?.parametric_attachment === "string" ? c.metadata.parametric_attachment : null;
}
const boxSize = (c: EditableModelComponent): Vec => {
  if (c.geometry.kind !== "box" || c.geometry.size.some(v => !Number.isFinite(v) || v <= 0)) throw new Error("Attachments require valid box reference members.");
  return c.geometry.size;
};
const close = (a: number, b: number) => Math.abs(a-b) < 1e-6;
function shapeEqual(a: unknown, b: unknown): boolean {
  if (typeof a === "number" && typeof b === "number") return close(a,b);
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v,i)=>shapeEqual(v,b[i]));
  if (a && b && typeof a === "object" && typeof b === "object") return Object.keys(a).length === Object.keys(b).length && Object.entries(a).every(([k,v])=>shapeEqual(v,(b as Record<string,unknown>)[k]));
  return a === b;
}

/** Deterministic solids in the existing document frame. No structural analysis. */
export function rebuildAttachments(doc: EditableModelDocument): EditableModelDocument {
  const definitions = attachments(doc);
  if (!definitions.length && !doc.components.some(attachmentOf)) return doc;
  if (definitions.length > 64) throw new Error("This editor supports at most 64 attached assemblies.");
  const next = structuredClone(doc), deck = doc.components.find(c=>c.id === `${prefix}platform-deck`);
  if (!deck) throw new Error("The platform deck reference is missing.");
  for(const name of ["platform-deck","beam-north","beam-south","beam-east","beam-west","column-ne","column-nw","column-se","column-sw"]) {
    const members=doc.components.filter(c=>c.id===`${prefix}${name}`);
    if(members.length!==1) throw new Error("Attached assemblies require the complete nine-member platform. Remove attachments before deleting core members.");
    boxSize(members[0]);
  }
  const ds = boxSize(deck), heading = deck.transform.rotation_deg[2], r = heading*Math.PI/180;
  const local = (c: EditableModelComponent): Vec => {
    if (c.transform.rotation_deg.slice(0,2).some(v=>!close(v,0)) || !close(c.transform.rotation_deg[2],heading) || c.transform.scale.some(v=>!close(v,1)) || c.transform.position.some(v=>!Number.isFinite(v))) throw new Error("Attachment reference members need a common horizontal rotation and unit scale.");
    const x=c.transform.position[0]-deck.transform.position[0], y=c.transform.position[1]-deck.transform.position[1];
    return [x*Math.cos(r)+y*Math.sin(r),-x*Math.sin(r)+y*Math.cos(r),c.transform.position[2]];
  };
  local(deck);
  const world = ([x,y,z]:Vec): Vec => [deck.transform.position[0]+x*Math.cos(r)-y*Math.sin(r),deck.transform.position[1]+x*Math.sin(r)+y*Math.cos(r),z];
  const ids = new Set<string>(), slots = new Set<string>();
  const old = new Map(doc.components.map(c=>[c.id,c]));
  next.components = next.components.filter(c=>!attachmentOf(c));
  const generated: EditableModelComponent[]=[];
  for (const a of definitions) {
    if (!a || typeof a.id !== "string" || !/^[a-zA-Z0-9_-]{1,80}$/.test(a.id) || ids.has(a.id) || !Object.hasOwn(ATTACHMENT_DEFAULTS,a.kind)) throw new Error("Invalid or duplicate attachment identity/type.");
    ids.add(a.id);
    const keys=Object.keys(ATTACHMENT_DEFAULTS[a.kind]);
    if (!a.parameters || Object.keys(a.parameters).length !== keys.length || keys.some(k=>!Number.isFinite(a.parameters[k]) || a.parameters[k]<=0 || a.parameters[k]>500)) throw new Error("Attachment dimensions must be finite, positive and at most 500 m (editor limit).");
    const count = a.kind === "brace" || a.kind === "connection" ? 2 : 1;
    if (!Array.isArray(a.refs) || a.refs.length !== count || new Set(a.refs).size !== count) throw new Error("Choose distinct valid component references.");
    const refs=a.refs.map(id=>doc.components.find(c=>c.id===id));
    if (refs.some(c=>!c || attachmentOf(c) || !c.id.startsWith(prefix))) throw new Error("An attachment references a missing or unsupported platform member.");
    const first=refs[0]!, second=refs[1], p=a.parameters, cs=boxSize(first), at=local(first), base=at[2]-cs[2]/2, top=at[2]+cs[2]/2;
    const slot=`${a.kind}:${a.refs.join(":")}`;
    if(slots.has(slot)) throw new Error("An assembly of this type already uses these references. Select and edit it instead.");
    slots.add(slot);
    if (a.kind !== "stairs" && first.category !== "column" || a.kind === "stairs" && first.id !== deck.id) throw new Error("Choose a column reference, or the deck for stairs.");
    const add=(part:string,category:string,geometry:EditableGeometry,position:Vec,color:string)=>{
      const id=`platform-addon:${a.id}:${part}`, previous=old.get(id);
      if(!attachmentOf(previous) && previous) throw new Error("Attachment component ID collides with an existing object.");
      const c: EditableModelComponent = {...previous,id,parent_id:first.id,name:previous?.name ?? `${a.kind.replaceAll("_"," ")} ${a.refs.map(id=>id.slice(prefix.length)).join(" → ")} · ${part}`,category,
        visible:previous?.visible ?? true,locked:previous?.locked ?? false,geometry,
        transform:{position:world(position),rotation_deg:[0,0,heading],scale:[1,1,1]},
        material:previous?.material ?? {name:"Conceptual / unverified",color,roughness:.75,metalness:category==="foundation"?0:.3},quantity:{...previous?.quantity,included:false},
        metadata:{...previous?.metadata,parametric_attachment:a.id,attachment_kind:a.kind,references:a.refs,engineering_status:"conceptual_unverified"}};
      if(previous?.locked && (!shapeEqual(previous.geometry,c.geometry) || !shapeEqual(previous.transform,c.transform))) throw new Error("Unlock the affected attached assembly before changing its geometry.");
      generated.push(c);
    };
    const box=(part:string,category:string,s:Vec,pos:Vec,color:string)=>add(part,category,{kind:"box",size:s},pos,color);
    if(a.kind === "foundation" || a.kind === "base_plate") {
      if(p.width<cs[0] || p.depth<cs[1]) throw new Error("Support width and depth must cover the column footprint.");
      const plate=definitions.find(d=>d.kind==="base_plate" && d.refs[0]===first.id);
      if(a.kind === "foundation" && plate && (p.width<plate.parameters.width || p.depth<plate.parameters.depth)) throw new Error("Foundation footprint must cover its base plate.");
      const offset=a.kind==="foundation" ? plate?.parameters.thickness ?? 0 : 0;
      box("body",a.kind,[p.width,p.depth,p.thickness],[at[0],at[1],base-offset-p.thickness/2],a.kind==="foundation"?"#a8a29e":"#cbd5e1");
    } else if(a.kind === "brace") {
      if(second?.category!=="column") throw new Error("Bracing connects two different column references in this milestone.");
      const end=local(second), es=boxSize(second);end[2]+=es[2]/2;
      if(p.radius>Math.min(cs[0],cs[1],es[0],es[1])/2) throw new Error("Brace diameter must fit the referenced column footprints.");
      const start:Vec=[at[0],at[1],base];
      if(Math.hypot(end[0]-start[0],end[1]-start[1])<1e-6 || end[2]<=base) throw new Error("Brace references must form a rising diagonal with positive horizontal span.");
      add("diagonal","bracing",{kind:"cylinder",start,end,radius_m:p.radius},[0,0,0],"#f59e0b");
    } else if(a.kind === "connection") {
      if(second?.category!=="beam") throw new Error("Connection placeholders require a column and beam reference.");
      const bp=local(second), bs=boxSize(second);
      if(!close(top,bp[2]-bs[2]/2) || Math.abs(at[0]-bp[0])>bs[0]/2 || Math.abs(at[1]-bp[1])>bs[1]/2) throw new Error("The referenced beam must touch the column top at this joint.");
      box("joint","connection",[p.width,p.depth,p.thickness],[at[0],at[1],top],"#d8b4fe");
    } else {
      const columns=doc.components.filter(c=>c.id.startsWith(`${prefix}column-`));
      if(columns.length!==4) throw new Error("Stairs need all four platform column references.");
      const bases=columns.map(c=>local(c)[2]-boxSize(c)[2]/2), ground=bases[0];
      if(bases.some(v=>!close(v,ground))) throw new Error("Stairs require a common column-base plane.");
      const rise=deck.transform.position[2]+ds[2]/2-ground;
      const n=Math.ceil(rise/p.maxRiser), riser=rise/n;
      if(rise<=0 || n<2 || n>200) throw new Error("Stairs require 2–200 risers with positive total rise (editor limit).");
      if(p.width>ds[0] || p.treadThickness>=riser || p.stringerRadius>=Math.min(p.width/4,riser/2)) throw new Error("Stair width must fit the deck; tread thickness and stringer radius must fit the riser and stair width.");
      for(let i=1;i<=n;i++) box(`tread-${i}`,"stairs",[p.width,p.going,p.treadThickness],[0,-ds[1]/2-(n-i+.5)*p.going,ground+i*riser-p.treadThickness/2],"#94a3b8");
      // Stringers pass beneath every tread. Their radius overlaps the tread underside;
      // first lower end extends to the local base plane, upper end supports the last
      // tread, whose end face touches the deck edge at deck-top height.
      for(const sign of [-1,1]) {
        const x=sign*(p.width/2-2*p.stringerRadius), z0=ground, z1=ground+rise-p.treadThickness;
        const y1=-ds[1]/2-p.going/2, slope=riser/p.going, y0=y1-(z1-z0)/slope;
        add(`stringer-${sign}`,"stairs",{kind:"cylinder",start:[x,y0,z0],end:[x,y1,z1],radius_m:p.stringerRadius},[0,0,0],"#64748b");
      }
    }
  }
  for(const c of doc.components.filter(attachmentOf)) if(!ids.has(attachmentOf(c)!)) throw new Error("A generated component has no attachment definition.");
  next.components.push(...generated);
  return next;
}

export function validateAttachments(doc: EditableModelDocument): string[] {
  try {
    const expected=rebuildAttachments(doc), actual=doc.components.filter(attachmentOf), wanted=expected.components.filter(attachmentOf);
    if(actual.length!==wanted.length) throw new Error("Generated assembly members are missing or duplicated. Use the attached component controls.");
    for(const c of wanted) {
      const a=actual.find(v=>v.id===c.id);
      if(!a || a.parent_id!==c.parent_id || a.category!==c.category || a.metadata?.attachment_kind!==c.metadata?.attachment_kind || a.metadata?.engineering_status!=="conceptual_unverified" || a.quantity?.included!==false || !shapeEqual(a.geometry,c.geometry) || !shapeEqual(a.transform,c.transform) || !shapeEqual(a.metadata?.references,c.metadata?.references)) throw new Error("Attached geometry or references are disconnected from their parameters. Edit through the attached component controls.");
    }
    return [];
  } catch(e) { return [(e as Error).message]; }
}

/** Add/edit/delete a parameter record, then regenerate actual solids as one draft. */
export function previewAttachment(doc: EditableModelDocument, item: Attachment | null, deleteId?: string): EditableModelDocument {
  const next=structuredClone(doc), items=attachments(doc);
  const id=deleteId ?? item?.id;
  if(!id) throw new Error("An attachment ID is required.");
  const existing=items.find(a=>a.id===id);
  if(existing && doc.components.some(c=>attachmentOf(c)===id && c.locked)) throw new Error("Unlock all parts of this assembly before editing or deleting it.");
  if(deleteId && !existing) throw new Error("The attachment to delete is missing.");
  const updated=items.filter(a=>a.id!==id);if(item)updated.push(item);
  next.generator_parameters={...next.generator_parameters,platform_attachments:{version:1,items:updated}};
  if(deleteId)next.components=next.components.filter(c=>attachmentOf(c)!==id);
  return rebuildAttachments(next);
}
