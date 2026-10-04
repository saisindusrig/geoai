"use client";

import { Box, Ruler, X } from "lucide-react";
import { formatAreaForUnit, formatDistanceForUnit } from "@/lib/geo";
import { useProjectStore } from "@/stores/projectStore";

export default function ObjectDetailsPanel() {
  const { selectedObject3d, setSelectedObject3d, measureUnit } = useProjectStore();
  if (!selectedObject3d) return null;

  const o = selectedObject3d;
  const rows: { label: string; value: string }[] = [
    { label: "Type", value: o.type },
    ...(o.material ? [{ label: "Material", value: o.material }] : []),
    ...(o.lengthM != null
      ? [{ label: "Length", value: formatDistanceForUnit(o.lengthM, measureUnit) }]
      : []),
    ...(o.widthM != null
      ? [{ label: "Width", value: formatDistanceForUnit(o.widthM, measureUnit) }]
      : []),
    ...(o.heightM != null ? [{ label: "Height", value: `${o.heightM.toFixed(1)} m` }] : []),
    ...(o.areaSqm != null
      ? [{ label: "Area", value: formatAreaForUnit(o.areaSqm, measureUnit) }]
      : []),
    ...(o.volumeM3 != null ? [{ label: "Volume", value: `${o.volumeM3.toFixed(0)} m³` }] : []),
    ...(o.quantity ? [{ label: "Est. quantity", value: o.quantity }] : []),
  ];

  return (
    <div className="pointer-events-auto panel-glass rounded-lg border border-border/80 shadow-lg w-[260px] overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-border/60 bg-card/90">
        <Box className="h-3.5 w-3.5 text-primary shrink-0" />
        <p className="text-[12px] font-semibold truncate flex-1">{o.name}</p>
        <button
          type="button"
          className="p-0.5 hover:bg-muted text-muted-foreground"
          onClick={() => setSelectedObject3d(null)}
          aria-label="Close"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
      <dl className="px-3 py-2 space-y-1.5 max-h-[280px] overflow-y-auto">
        {rows.map(({ label, value }) => (
          <div key={label} className="flex justify-between gap-2 text-[11px]">
            <dt className="text-muted-foreground shrink-0">{label}</dt>
            <dd className="font-data text-right text-foreground">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="px-3 py-2 border-t border-border/40 flex items-center gap-1 text-[10px] text-muted-foreground">
        <Ruler className="h-3 w-3" />
        Click another object to inspect
      </div>
    </div>
  );
}
