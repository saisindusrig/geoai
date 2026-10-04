"use client";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

export default function TransformOptions({ editor }: { editor: EditableModelEditor }) {
  return <details className="relative text-[10px]">
    <summary title="Transform settings: coordinates, pivot and snapping" className="cursor-pointer rounded-sm border border-white/10 bg-background/90 px-2 py-1">{editor.coordinateMode.toUpperCase()} · {editor.tool === "rotate" ? `${editor.rotationSnap || "Off"}°` : editor.tool === "scale" ? editor.scaleSnap || "Off" : `${editor.snapMeters || "Off"} m`} <span role="status" aria-label={editor.saveError ? "Save failed" : editor.saving ? "Saving" : editor.dirty ? "Unsaved" : "Saved"} title={editor.saveError ? "Save failed" : editor.saving ? "Saving…" : editor.dirty ? "Unsaved" : "Saved"} className={`ml-1 inline-block size-1.5 rounded-full ${editor.saveError ? "bg-red-400" : editor.dirty ? "bg-amber-300" : "bg-primary"}`} /></summary>
    <div className="absolute bottom-full right-0 mb-2 z-40 max-h-[65vh] w-52 space-y-2 overflow-y-auto rounded-sm border border-border bg-background-secondary p-2 shadow-xl">
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
