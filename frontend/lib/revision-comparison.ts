import type { EditableModelDocument } from "./types";
export function compareDocuments(previous:EditableModelDocument,current:EditableModelDocument){
  const before=new Map(previous.components.map(item=>[item.id,item])),after=new Map(current.components.map(item=>[item.id,item]));
  return [...new Set([...before.keys(),...after.keys()])].map(id=>{
    const a=before.get(id),b=after.get(id);
    const status=!a?"ADDED":!b?"REMOVED":JSON.stringify(a)===JSON.stringify(b)?"UNCHANGED":"MODIFIED";
    return {id,name:b?.name ?? a!.name,status,
      position:a&&b?b.transform.position.map((value,index)=>value-a.transform.position[index]):null,
      heading:a&&b?b.transform.rotation_deg[2]-a.transform.rotation_deg[2]:null,
      scale:a&&b?b.transform.scale.map((value,index)=>value-a.transform.scale[index]):null,
      geometryChanged:!!a&&!!b&&JSON.stringify(a.geometry)!==JSON.stringify(b.geometry)};
  });
}
