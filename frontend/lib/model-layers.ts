import type { ModelLayerVisibility } from "@/stores/projectStore";

export interface ModelLayerDef {
  key: keyof ModelLayerVisibility;
  label: string;
  group: string;
}

export const MODEL_LAYER_DEFS: ModelLayerDef[] = [
  { key: "outer", label: "Terrain", group: "Site" },
  { key: "traffic", label: "Roads / Traffic", group: "Site" },
  { key: "foundation", label: "Foundation", group: "Structure" },
  { key: "inner", label: "Structure", group: "Structure" },
  { key: "steel", label: "Reinforcement", group: "Structure" },
  { key: "concrete", label: "Concrete", group: "Structure" },
  { key: "electrical", label: "Electrical", group: "MEP" },
  { key: "drainage", label: "Drainage", group: "MEP" },
  { key: "pipeline", label: "Plumbing", group: "MEP" },
];

export const MODEL_LAYER_GROUPS = [...new Set(MODEL_LAYER_DEFS.map((l) => l.group))];
