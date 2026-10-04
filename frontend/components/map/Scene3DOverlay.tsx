"use client";

import Scene3DLayerPanel from "@/components/map/Scene3DLayerPanel";
import ObjectDetailsPanel from "@/components/map/ObjectDetailsPanel";
import { useProjectStore } from "@/stores/projectStore";

/** Floating 3D scene chrome: layer panel (left), object inspector (right). */
export default function Scene3DOverlay() {
  const scene3dMeasureReadout = useProjectStore((s) => s.scene3dMeasureReadout);

  return (
    <>
      <div className="absolute top-16 left-3 z-20 w-[200px] max-h-[calc(100%-8rem)] overflow-y-auto pointer-events-auto panel-glass rounded-lg p-2 md:hidden">
        <Scene3DLayerPanel compact />
      </div>

      <div className="absolute top-16 right-3 z-20 pointer-events-none hidden lg:block">
        <ObjectDetailsPanel />
      </div>

      {scene3dMeasureReadout && (
        <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-20 pointer-events-none panel-glass rounded-md px-3 py-1.5 text-xs font-data text-accent">
          {scene3dMeasureReadout}
        </div>
      )}
    </>
  );
}
