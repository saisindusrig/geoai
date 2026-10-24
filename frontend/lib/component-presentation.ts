import type { EditableModelComponent } from "./types";

/** Display labels only: never rewrite component identity or saved names. */
export function componentDisplayName(component: EditableModelComponent) {
  if (component.name === "platform-deck") return "Slab";
  const tread=component.id.match(/:tread-(\d+)$/);if(tread)return `Stair ${tread[1].padStart(2,"0")} · tread`;
  const stringer=component.id.match(/:stringer-(.+)$/);if(stringer)return `Stair stringer ${stringer[1]}`;
  const refs=component.metadata?.references;
  const corner=Array.isArray(refs) ? String(refs[0]).match(/column[-:](nw|ne|sw|se)$/i)?.[1]?.toUpperCase() : undefined;
  const role=componentRole(component);
  if(corner && /foundation|footing|base plate|connection/.test(role))return `${/foundation|footing/.test(role)?"Footing":/base plate/.test(role)?"Base plate":"Connection"} ${corner}`;
  return component.name.replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, "")
    .replace(/\s*[·�]\s*body\b/gi, "").replace(/\s*[·�]\s*/g, " ").replace(/[-_]/g, " ")
    .replace(/\s+/g, " ").trim().replace(/\b(ne|nw|se|sw)\b/gi, value => value.toUpperCase()).replace(/\b(north|south|east|west)\b/gi, value=>value[0].toUpperCase()+value.slice(1).toLowerCase()).replace(/^./, value => value.toUpperCase());
}
export function componentRole(component: EditableModelComponent) {
  return String(component.metadata?.attachment_kind ?? component.metadata?.componentRole ?? component.category).replaceAll("_", " ").toLowerCase();
}
