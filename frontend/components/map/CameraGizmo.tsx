"use client";
import type { Viewer } from "cesium";
import { useEffect, useState } from "react";
import { useProjectStore } from "@/stores/projectStore";
const axes = [
  { name: "X", color: "#ee465b", vector: [1, 0, 0], heading: 270, pitch: 0 },
  { name: "Y", color: "#89bd20", vector: [0, 1, 0], heading: 180, pitch: 0 },
  { name: "Z", color: "#3189ef", vector: [0, 0, 1], heading: 0, pitch: -90 },
] as const;
type Endpoint = { x: number; y: number; depth: number; axis: number; positive: boolean };
export default function CameraGizmo({ viewer, Cesium, longitude, latitude }: {
  viewer: Viewer; Cesium: typeof import("cesium"); longitude: number; latitude: number;
}) {
  const [points, setPoints] = useState<Endpoint[]>([]);
  const underground = useProjectStore(state => state.undergroundView);
  useEffect(() => {
    if (viewer.isDestroyed()) return;
    const frame = Cesium.Transforms.eastNorthUpToFixedFrame(Cesium.Cartesian3.fromDegrees(longitude, latitude));
    let lastPose = "";
    const update = () => {
      const camera = viewer.camera;
      const pose = [camera.heading, camera.pitch, camera.roll].map(value => value.toFixed(4)).join(",");
      if (pose === lastPose) return;
      lastPose = pose;
      const next: Endpoint[] = [];
      axes.forEach((axis, index) => {
        const direction = Cesium.Matrix4.multiplyByPointAsVector(frame, new Cesium.Cartesian3(...axis.vector), new Cesium.Cartesian3());
        for (const sign of [-1, 1]) next.push({ axis: index, positive: sign === 1,
          x: 54 + sign * Cesium.Cartesian3.dot(direction, camera.rightWC) * 34,
          y: 54 - sign * Cesium.Cartesian3.dot(direction, camera.upWC) * 34,
          depth: sign * Cesium.Cartesian3.dot(direction, camera.directionWC) });
      });
      // Keep all six controls reachable when projected axes coincide head-on.
      for (let pass = 0; pass < 12; pass++) {
        for (let i = 0; i < next.length; i++) for (let j = i + 1; j < next.length; j++) {
          const a = next[i], b = next[j], dx = b.x - a.x, dy = b.y - a.y;
          const distance = Math.hypot(dx, dy);
          if (distance >= 29) continue;
          const ux = distance > .01 ? dx / distance : 1;
          const uy = distance > .01 ? dy / distance : 0;
          const shift = (29 - distance) / 2;
          a.x = Math.max(14, Math.min(94, a.x - ux * shift));
          a.y = Math.max(14, Math.min(94, a.y - uy * shift));
          b.x = Math.max(14, Math.min(94, b.x + ux * shift));
          b.y = Math.max(14, Math.min(94, b.y + uy * shift));
        }
      }
      setPoints(next.sort((a, b) => b.depth - a.depth));
    };
    update();
    return viewer.scene.postRender.addEventListener(update);
  }, [viewer, Cesium, longitude, latitude]);
  const orient = (axis: number, positive: boolean) => {
    if (viewer.isDestroyed()) return;
    if (viewer.canvas?.dataset?.navigationMode) {
      const selected = axes[axis];
      window.dispatchEvent(new CustomEvent("geoai:orient-view", {detail:{heading:selected.heading + (positive || axis === 2 ? 0 : 180),pitch:axis === 2 && !positive ? 90 : axis !== 2 && !underground ? -5 : selected.pitch}}));
      return;
    }
    const ray = viewer.camera.getPickRay(new Cesium.Cartesian2(viewer.canvas.clientWidth / 2, viewer.canvas.clientHeight / 2));
    const center = ray && viewer.scene.globe.pick(ray, viewer.scene);
    const ground = viewer.scene.globe.getHeight(Cesium.Cartographic.fromDegrees(longitude, latitude)) ?? 0;
    const target = center ?? Cesium.Cartesian3.fromDegrees(longitude, latitude, ground);
    const range = Math.max(50, Cesium.Cartesian3.distance(viewer.camera.positionWC, target));
    const selected = axes[axis];
    viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(target, 1), {
      offset: new Cesium.HeadingPitchRange(Cesium.Math.toRadians(selected.heading + (positive || axis === 2 ? 0 : 180)), Cesium.Math.toRadians(axis === 2 && !positive ? 90 : axis !== 2 && !underground ? -5 : selected.pitch), range),
      duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : .6,
    });
  };
  return <div role="group" aria-label="Camera orientation gizmo" className="absolute right-3 top-3 z-40 w-[118px] select-none">
    <div className="relative size-[118px]">
      <svg viewBox="0 0 108 108" className="absolute inset-0 size-full pointer-events-none" aria-hidden="true">
        <circle cx="54" cy="54" r="43" fill="none" stroke="#94a3b8" strokeOpacity=".12" />
        {points.map(point => <line key={`${point.axis}-${point.positive}`} x1="54" y1="54" x2={point.x} y2={point.y} stroke={axes[point.axis].color} strokeOpacity={point.positive ? .9 : .3} strokeWidth={point.positive ? 2 : 1} strokeDasharray={point.positive ? undefined : "2 3"} />)}
        <circle cx="54" cy="54" r="4" fill="#cbd5e1" />
      </svg>
      {points.map((point, index) => {
        const axis = axes[point.axis];
        const blocked = point.axis === 2 && !point.positive && !underground;
        return <button key={`${point.axis}-${point.positive}`} type="button" disabled={blocked}
          title={blocked ? "Enable explicit underground view to inspect from below" : `${point.positive ? "+" : "−"}${axis.name} view`}
          aria-label={`${point.positive ? "Positive" : "Negative"} ${axis.name} axis view`}
          onClick={() => orient(point.axis, point.positive)}
          className="absolute grid size-7 min-h-7 min-w-7 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border text-[10px] font-bold shadow-md transition-[background-color,box-shadow] hover:ring-2 hover:ring-white/50 disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          style={{ left: `${point.x / 108 * 100}%`, top: `${point.y / 108 * 100}%`, zIndex: index + 1, borderColor: axis.color, background: point.positive ? axis.color : "#111c2d", color: point.positive ? "#07111f" : axis.color }}>
          {point.positive ? "+" : "−"}{axis.name}
        </button>;
      })}
    </div>
  </div>;
}
