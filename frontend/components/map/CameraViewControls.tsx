"use client";
import { useEffect, useState } from "react";
import styles from "./WorkspacePanels.module.css";
import type { Viewer } from "cesium";
import { api, formatApiErrorMessage } from "@/lib/api";

interface SavedView { id: number; name: string; position: [number, number, number]; heading: number; pitch: number; roll: number; projection: "PERSPECTIVE" | "ORTHOGRAPHIC" }

export default function CameraViewControls({ viewer, Cesium, projectId, longitude, latitude }: { viewer: Viewer; Cesium: typeof import("cesium"); projectId?: number; longitude: number; latitude: number }) {
  const [views, setViews] = useState<SavedView[]>([]);
  const [name, setName] = useState("SITE");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    api.get<SavedView[]>(`/api/projects/${projectId}/engineering/camera-views`).then((result) => { if (!cancelled) setViews(result); }).catch((reason) => { if (!cancelled) setError(formatApiErrorMessage(reason)); });
    return () => { cancelled = true; };
  }, [projectId]);
  async function save() {
    if (!projectId || viewer.isDestroyed() || saving || !name.trim()) return;
    setSaving(true); setSaved(false);
    const camera = viewer.camera;
    const payload = { name: name.trim(), position: [camera.positionWC.x, camera.positionWC.y, camera.positionWC.z], heading: camera.heading, pitch: camera.pitch, roll: camera.roll, projection: camera.frustum instanceof Cesium.OrthographicFrustum ? "ORTHOGRAPHIC" : "PERSPECTIVE" };
    try {
      await api.post(`/api/projects/${projectId}/engineering/camera-views`, payload);
      setViews(await api.get<SavedView[]>(`/api/projects/${projectId}/engineering/camera-views`));
      setError(null); setSaved(true);
    } catch (reason) { setError(formatApiErrorMessage(reason)); }
    finally { setSaving(false); }
  }
  return <div className="space-y-4">
    <p className={styles.muted}>Frame the site from a preset angle or save your current viewpoint.</p>
    <div className="grid grid-cols-3 gap-2">{[["SITE",0,-55],["TOP",0,-90],["FRONT",0,0],["LEFT",90,0],["RIGHT",270,0],["ALIGNMENT",0,-20],["FOUNDATION",0,-10]].map(([label, heading, pitch]) => <button key={label} className={styles.button} onClick={() => {
      if (viewer.isDestroyed()) return;
      const ground = viewer.scene.globe.getHeight(Cesium.Cartographic.fromDegrees(longitude, latitude)) ?? 0;
      viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(Cesium.Cartesian3.fromDegrees(longitude, latitude, ground), 100), { offset: new Cesium.HeadingPitchRange(Cesium.Math.toRadians(Number(heading)), Cesium.Math.toRadians(Number(pitch)), label === "FOUNDATION" ? 100 : 400), duration: .7 });
      setName(String(label));
    }}>{label}</button>)}</div>
    {projectId && <><input aria-label="Camera view name" className={styles.input} value={name} onChange={(e) => setName(e.target.value)} /><button className={styles.primary} disabled={saving || !name.trim()} onClick={() => void save()}>{saving ? "Saving viewpoint…" : "Save current camera"}</button>{saved && <p role="status" className={styles.muted}>Viewpoint saved to this project.</p>}</>}
    {views.length > 0 && <p className={styles.eyebrow}>Saved viewpoints</p>}
    {views.map((view) => <button key={view.id} className={`${styles.button} mr-2 mb-2`} onClick={() => {
      if (viewer.isDestroyed()) return;
      if (view.projection === "ORTHOGRAPHIC") viewer.camera.switchToOrthographicFrustum(); else viewer.camera.switchToPerspectiveFrustum();
      viewer.camera.setView({ destination: new Cesium.Cartesian3(...view.position), orientation: { heading: view.heading, pitch: view.pitch, roll: view.roll } });
      viewer.scene.requestRender();
    }}>{view.name}</button>)}
    {error && <p role="alert" className={styles.notice}>{error}</p>}
  </div>;
}
