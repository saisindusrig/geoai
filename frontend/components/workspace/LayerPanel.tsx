"use client";

import { type LayerVisibility, useProjectStore } from "@/stores/projectStore";

const LAYERS: { key: keyof LayerVisibility; label: string }[] = [
  { key: "satellite", label: "Satellite imagery" },
  { key: "roads", label: "Roads (OSM)" },
  { key: "buildings", label: "Buildings (OSM context)" },
  { key: "terrain", label: "Terrain" },
  { key: "tiles3d", label: "3D city tiles" },
  { key: "projectModel", label: "Generated model" },
  { key: "excavation", label: "Excavation" },
  { key: "utilities", label: "Utility / pipeline" },
];

export default function LayerPanel() {
  const { layers, toggleLayer } = useProjectStore();
  return (
    <div className="space-y-1">
      {LAYERS.map((l) => (
        <label
          key={l.key}
          className="flex items-center gap-2 text-xs py-0.5 cursor-pointer select-none"
        >
          <input
            type="checkbox"
            checked={layers[l.key]}
            onChange={() => toggleLayer(l.key)}
            className="accent-sky-600"
          />
          {l.label}
        </label>
      ))}
    </div>
  );
}
