import { Color } from "three";
import type { EditableModelComponent } from "./types";
import { componentRole } from "./component-presentation";

/** Presentation palette only. Never use this classification in analysis or exports. */
export function displayMaterial(component: EditableModelComponent) {
  const tint = (color: string) => new Color(component.material.color).lerp(new Color(color), 0.78).getStyle();
  const name = component.material.name.toLowerCase();
  const role = componentRole(component);
  // Familiar role finishes are illustrative, including conceptual components.
  // Authored material declarations are unchanged and never certified here.
  if (/soil|earth|ground/.test(name)) return {color:tint("#997653"),finish:"Soil appearance"};
  if (/slab|foundation|footing/.test(role)) return {color:tint(role.includes("slab") ? "#d6d0c1" : "#b4ac9b"),finish:"Concrete-style appearance"};
  if (/column/.test(role)) return {color:tint("#587b96"),finish:"Steel-style column appearance"};
  if (/beam/.test(role)) return {color:tint("#7c9cac"),finish:"Steel-style beam appearance"};
  if (/base plate|connection/.test(role)) return {color:tint("#b1b5b4"),finish:"Connection appearance"};
  if (/stair/.test(role)) return {color:tint("#b3bfc0"),finish:"Stair appearance"};
  if (/\b(concrete|rc|rcc)\b/.test(name)) return { color: tint("#b5b4aa"), finish: "Concrete appearance" };
  if (/\b(soil|earth|ground)\b/.test(name)) return { color: tint("#aa8057"), finish: "Soil appearance" };
  if (/\b(steel|metal)\b/.test(name)) return { color: tint("#829bb2"), finish: "Steel appearance" };
  if (/\b(concept|conceptual|placeholder)\b/.test(name)) return { color: tint("#8bacc5"), finish: "Conceptual appearance" };
  return { color: component.material.color, finish: "Authored appearance" };
}
