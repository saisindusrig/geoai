"use client";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

export default function TransformOptions({ editor }: { editor: EditableModelEditor }) {
  return <details className="relative text-[10px]">
    <summary className="cursor-pointer rounded-sm border border-white/10 bg-background/90 px-3 py-2">{editor.coordinateMode.toUpperCase()} · SNAP {editor.tool === "rotate" ? `${editor.rotationSnap || "Off"}°` : editor.tool === "scale" ? editor.scaleSnap || "Off" : `${editor.snapMeters || "Off"} m`} <span role="status" className="ml-2 text-[9px] text-muted-foreground">{editor.saveError ? "Save failed" : editor.saving ? "Saving…" : editor.dirty ? "Unsaved" : "Saved"}</span></summary>
    <div className="absolute left-0 top-10 z-40 w-52 space-y-3 rounded-sm border border-border bg-background-secondary p-3 shadow-xl">
      <label className="block">Coordinates<select aria-label="Transform coordinates" value={editor.coordinateMode} onChange={event => editor.setCoordinateMode(event.target.value as "local" | "world")} className="mt-1 h-8 w-full border border-border bg-background"><option value="local">Local ENU</option><option value="world">World ECEF</option></select></label>
      <label className="block">Pivot<select aria-label="Transform pivot" value={editor.pivotMode} onChange={event => editor.setPivotMode(event.target.value as "active" | "median" | "individual")} className="mt-1 h-8 w-full border border-border bg-background"><option value="active">Active</option><option value="median">Median</option><option value="individual">Individual origins</option></select></label>
      {([
        ["Translation snap", editor.snapMeters, editor.setSnapMeters, [0,0.01,0.1,0.5,1,5,10], " m"],
        ["Rotation snap", editor.rotationSnap, editor.setRotationSnap, [0,1,5,15,30,45,90], "°"],
        ["Scale snap", editor.scaleSnap, editor.setScaleSnap, [0,0.01,0.05,0.1,0.25], ""],
      ] as const).map(([name,value,set,options,unit]) => <label key={name} className="block">{name}<select aria-label={name} value={value} onChange={event => set(Number(event.target.value))} className="mt-1 h-8 w-full border border-border bg-background">{options.map(option => <option key={option} value={option}>{option ? `${option}${unit}` : "Off"}</option>)}</select></label>)}
      <p className="text-muted-foreground">World uses Earth-fixed axes. Axis scaling is unavailable when it would introduce shear; uniform scaling preserves the model.</p>
      <p className="text-muted-foreground">Hold Alt while moving to snap to the project origin, editable endpoints and component centers. Alignment endpoints and 20 m stations snap in plan; they supply no ground elevation.</p>
    </div>
  </details>;
}
