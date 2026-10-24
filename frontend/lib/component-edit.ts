import type { EditableModelComponent } from "./types";

/** Only changed, permitted fields are submitted to the existing editor gate. */
export function componentEditPatch(original: EditableModelComponent, draft: EditableModelComponent): Partial<EditableModelComponent> {
  const patch: Partial<EditableModelComponent> = {};
  for (const key of ["name", "transform", "geometry", "material"] as const) {
    if (JSON.stringify(original[key]) !== JSON.stringify(draft[key])) Object.assign(patch, {[key]: draft[key]});
  }
  return patch;
}
