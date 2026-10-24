import type { EditableModelDocument, EditableModelComponent } from "./types";
import { rebuildAttachments } from "./platform-attachments";

export type PlatformParameters = { length: number; width: number; height: number; slabThickness: number; beamWidth: number; beamDepth: number; columnWidth: number; columnDepth: number };
const names = ["platform-deck", "beam-north", "beam-south", "beam-east", "beam-west", "column-ne", "column-nw", "column-se", "column-sw"];
export function platformMembers(doc: EditableModelDocument) {
  const members = names.map(name => doc.components.filter(c => c.id === `industrial-platform-5x3:${name}`));
  return members.every(items => items.length === 1 && items[0].geometry.kind === "box") ? members.map(items => items[0]) : null;
}
function size(c: EditableModelComponent): [number, number, number] { if(c.geometry.kind !== "box") throw new Error("Box member required."); return c.geometry.size; }
export function readPlatform(doc: EditableModelDocument): PlatformParameters | null {
  const m = platformMembers(doc); if (!m) return null;
  const [deck, beam, , , , column] = m;
  const base = column.transform.position[2] - size(column)[2] / 2;
  return { length:size(deck)[0], width:size(deck)[1], height:deck.transform.position[2]+size(deck)[2]/2-base,
    slabThickness:size(deck)[2], beamWidth:size(beam)[1], beamDepth:size(beam)[2], columnWidth:size(column)[0], columnDepth:size(column)[1] };
}
export function previewPlatform(doc: EditableModelDocument, p: PlatformParameters): EditableModelDocument {
  const m = platformMembers(doc); if (!m) throw new Error("The complete nine-member maintenance platform is required.");
  if (Object.values(p).some(v => !Number.isFinite(v) || v <= 0)) throw new Error("All dimensions must be finite and greater than zero.");
  if (m.some(c => c.locked)) throw new Error("Unlock all platform members before editing the assembly.");
  const deck = m[0], angle = deck.transform.rotation_deg[2];
  if (m.some(c => c.transform.scale.some(v => Math.abs(v-1)>1e-8) || c.transform.rotation_deg.slice(0,2).some(v => Math.abs(v)>1e-8) || Math.abs(c.transform.rotation_deg[2]-angle)>1e-8)) throw new Error("Platform members must have unit scale and a common horizontal rotation. Undo individual scale or rotation edits first.");
  const x = (p.length-Math.max(p.beamWidth,p.columnWidth))/2, y=(p.width-Math.max(p.beamWidth,p.columnDepth))/2;
  const endSpan=2*y-p.beamWidth, columnHeight=p.height-p.slabThickness-p.beamDepth;
  if (x<=p.beamWidth/2 || endSpan<=0) throw new Error("The footprint must leave a positive clear span between the perimeter beams and columns.");
  if (columnHeight<=0) throw new Error("Deck height must exceed slab thickness plus beam depth.");
  const base=m[5].transform.position[2]-size(m[5])[2]/2;
  if(m.slice(5).some(c => Math.abs(c.transform.position[2]-size(c)[2]/2-base)>1e-6)) throw new Error("All four column bases must share the same local reference plane.");
  const next=structuredClone(doc), radians=angle*Math.PI/180;
  const set=(name:string, xyz:[number,number,number], dimensions:[number,number,number])=>{
    const c=next.components.find(c=>c.id===`industrial-platform-5x3:${name}`)!;
    c.geometry={kind:"box",size:dimensions};
    c.transform.position=[deck.transform.position[0]+xyz[0]*Math.cos(radians)-xyz[1]*Math.sin(radians),deck.transform.position[1]+xyz[0]*Math.sin(radians)+xyz[1]*Math.cos(radians),base+xyz[2]];
    c.metadata={...c.metadata,engineering_status:"conceptual_unverified"};
  };
  set("platform-deck",[0,0,p.height-p.slabThickness/2],[p.length,p.width,p.slabThickness]);
  for(const [name,sign] of [["beam-north",1],["beam-south",-1]] as const) set(name,[0,sign*y,columnHeight+p.beamDepth/2],[p.length,p.beamWidth,p.beamDepth]);
  for(const [name,sign] of [["beam-east",1],["beam-west",-1]] as const) set(name,[sign*x,0,columnHeight+p.beamDepth/2],[p.beamWidth,endSpan,p.beamDepth]);
  for(const [name,sx,sy] of [["column-ne",1,1],["column-nw",-1,1],["column-se",1,-1],["column-sw",-1,-1]] as const) set(name,[sx*x,sy*y,columnHeight/2],[p.columnWidth,p.columnDepth,columnHeight]);
  next.generator_parameters={...next.generator_parameters,maintenance_platform:{version:1,parameters:p,status:"conceptual_unverified"}};
  return rebuildAttachments(next);
}
