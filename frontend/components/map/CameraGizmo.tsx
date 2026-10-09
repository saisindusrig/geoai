"use client";

import type { Viewer } from "cesium";
import { useEffect, useState } from "react";

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
        for (const sign of [-1, 1]) next.push({
          axis: index, positive: sign === 1,
          x: 54 + sign * Cesium.Cartesian3.dot(direction, camera.rightWC) * 34,
          y: 54 - sign * Cesium.Cartesian3.dot(direction, camera.upWC) * 34,
          depth: sign * Cesium.Cartesian3.dot(direction, camera.directionWC),
        });
      });
      setPoints(next.sort((a, b) => b.depth - a.depth));
    };
    update();
    return viewer.scene.postRender.addEventListener(update);
  }, [viewer, Cesium, longitude, latitude]);
  const orient = (axis: number, positive: boolean) => {
    if (viewer.isDestroyed()) return;
    const ray = viewer.camera.getPickRay(new Cesium.Cartesian2(viewer.canvas.clientWidth / 2, viewer.canvas.clientHeight / 2));
    const center = ray && viewer.scene.globe.pick(ray, viewer.scene);
    const ground = viewer.scene.globe.getHeight(Cesium.Cartographic.fromDegrees(longitude, latitude)) ?? 0;
    const target = center ?? Cesium.Cartesian3.fromDegrees(longitude, latitude, ground);
    const range = Math.max(50, Cesium.Cartesian3.distance(viewer.camera.positionWC, target));
    const selected = axes[axis];
    viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(target, 1), {
      offset: new Cesium.HeadingPitchRange(Cesium.Math.toRadians(selected.heading + (positive || axis === 2 ? 0 : 180)), Cesium.Math.toRadians(axis === 2 && !positive ? 90 : selected.pitch), range),
      duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : .6,
    });
  };
  return <div role="group" aria-label="Camera orientation gizmo" className="absolute right-3 top-3 z-40 size-[108px] select-none">
    <svg viewBox="0 0 108 108" className="absolute inset-0 size-full" aria-hidden="true">
      <circle cx="54" cy="54" r="43" fill="#101613" fillOpacity=".18" />
      {points.filter(point => point.positive).map(point => <line key={point.axis} x1="54" y1="54" x2={point.x} y2={point.y} stroke={axes[point.axis].color} strokeWidth="2" />)}
      <circle cx="54" cy="54" r="3" fill="#b8c3b9" />
    </svg>
    {points.map(point => <button key={`${point.axis}-${point.positive}`} type="button" title={`${point.positive ? "+" : "−"}${axes[point.axis].name} view`} aria-label={`${point.positive ? "Positive" : "Negative"} ${axes[point.axis].name} axis view`} onClick={() => orient(point.axis, point.positive)}
      className="absolute grid size-[20px] -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full text-[11px] font-bold transition-[filter,box-shadow] hover:brightness-125 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
      style={{ left: point.x, top: point.y, border: `2px solid ${axes[point.axis].color}`, background: point.positive ? axes[point.axis].color : "#18221ad9", color: "#132017", boxShadow: "0 1px 4px #0005" }}>
      {point.positive ? axes[point.axis].name : ""}
    </button>)}
  </div>;
}
