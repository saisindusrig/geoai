"use client";

/* eslint-disable react-hooks/immutability -- Cesium Viewer is an external imperative engine; effects intentionally update its clock and renderer. */

import { useEffect, useRef, useState } from "react";
import CameraGizmo from "./CameraGizmo";
import { createPortal } from "react-dom";
import { useWorkspaceMap } from "@/components/layout/WorkspaceMapContext";

import { Sun, X, Layers3, Camera, Activity, Globe2, Play, Pause, RotateCcw } from "lucide-react";

import type { Viewer } from "cesium";

import { api, formatApiErrorMessage } from "@/lib/api";

import { useProjectStore } from "@/stores/projectStore";
import { useWorkspacePanel } from "@/hooks/useWorkspacePanel";
import styles from "./WorkspacePanels.module.css";
import CameraViewControls from "@/components/map/CameraViewControls";
import WorkspaceMapControl from "@/components/layout/WorkspaceMapControl";

import { localDateTimeToUtc, localDateTimeValue, sunAnglesFromEnu, scenePresetPreferences, type ScenePreset, type EngineeringMapPreferences } from "@/lib/sun-study";



export default function SunStudyControls({ viewer, Cesium, longitude, latitude, projectId, buildingsAvailable, terrainAvailable }: {

  viewer: Viewer; Cesium: typeof import("cesium"); longitude: number; latitude: number; projectId?: number; buildingsAvailable: boolean; terrainAvailable: boolean;

}) {

  const { rightControlsContainer } = useWorkspaceMap();
  const panelContainer = rightControlsContainer?.closest(".workspace-map-viewport");
  const layers = useProjectStore((state) => state.layers);
  const toggleLayer = useProjectStore((state) => state.toggleLayer);
  const { open, close, toggle } = useWorkspacePanel("scene");
  const [tab, setTab] = useState("Scene");
  useEffect(() => {
    if (!open) return;
    const dismiss = (event: PointerEvent) => {
      if (!(event.target instanceof Element) || !event.target.closest('[data-workspace-popup="scene"], [aria-label="Scene / Sun study"]')) close();
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [open, close]);
  useEffect(() => {
    const openControls = () => { setTab("Scene"); toggle(); };
    window.addEventListener("geoai:open-scene-controls", openControls);
    return () => window.removeEventListener("geoai:open-scene-controls", openControls);
  }, [toggle]);

  const [preferences, setPreferences] = useState<EngineeringMapPreferences>(() => ({ preset: "ENGINEERING", quality: "BALANCED", shadows: "OFF", utc: new Date().toISOString(), timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone }));

  const [ready, setReady] = useState(!projectId);

  const [, setSaveStatus] = useState(projectId ? "Loading settings…" : "Session settings");
  const [retry, setRetry] = useState(0);
  const [playing, setPlaying] = useState(false);

  const [speed, setSpeed] = useState(60);

  const [error, setError] = useState<string | null>(null);

  const [readout, setReadout] = useState<{ azimuth: number; elevation: number; local: string; utc: string } | null>(null);

  const [zoneDraft, setZoneDraft] = useState(preferences.timeZone);

  const preferencesEdited = useRef(false);

  useEffect(() => {

    if (!projectId) return;

    let cancelled = false;

    api.get<{ preferences: EngineeringMapPreferences | null }>(`/api/projects/${projectId}/engineering/map-preferences`).then((result) => {

      if (!cancelled && result.preferences && !preferencesEdited.current) { setPreferences(result.preferences); setZoneDraft(result.preferences.timeZone); }

      if (!cancelled) { setReady(true); setSaveStatus("Project settings loaded"); }

    }).catch((reason) => { if (!cancelled) setError(formatApiErrorMessage(reason)); });

    return () => { cancelled = true; };

  }, [projectId, retry]);

  useEffect(() => {

    if (!ready || !projectId || !preferencesEdited.current) return;

    let cancelled = false;
    const timer = setTimeout(() => {
      setSaveStatus("Saving…");
      void api.put(`/api/projects/${projectId}/engineering/map-preferences`, preferences).then(() => {
        if (!cancelled) { setSaveStatus("Saved to project"); setError(null); }
      }).catch((reason) => { if (!cancelled) { setError(formatApiErrorMessage(reason)); setSaveStatus("Changes not saved"); } });
    }, 750);

    return () => { cancelled = true; clearTimeout(timer); };

  }, [preferences, projectId, ready, retry]);

  useEffect(() => {

    if (viewer.isDestroyed()) return;

    viewer.clock.currentTime = Cesium.JulianDate.fromIso8601(preferences.utc);

    viewer.clock.clockStep = Cesium.ClockStep.SYSTEM_CLOCK_MULTIPLIER;
    viewer.scene.requestRender();

  }, [preferences.utc, viewer, Cesium]);

  useEffect(() => {

    if (viewer.isDestroyed()) return;

    viewer.scene.globe.enableLighting = preferences.preset !== "ENGINEERING" && preferences.preset !== "SURVEY_QA";



    viewer.shadows = preferences.shadows !== "OFF";

    viewer.terrainShadows = preferences.shadows === "OFF" ? Cesium.ShadowMode.DISABLED : Cesium.ShadowMode.ENABLED;

    viewer.shadowMap.softShadows = preferences.shadows !== "OFF";

    viewer.shadowMap.size = preferences.shadows === "HIGH" ? 4096 : 2048;

    viewer.resolutionScale = preferences.quality === "PERFORMANCE" ? .75 : preferences.quality === "HIGH_DETAIL" ? 1.25 : 1;

    viewer.scene.globe.maximumScreenSpaceError = preferences.quality === "PERFORMANCE" ? 4 : preferences.quality === "HIGH_DETAIL" ? 1 : 2;

    viewer.scene.requestRenderMode = preferences.quality === "PERFORMANCE";

    viewer.scene.requestRender();

  }, [preferences.preset, preferences.shadows, preferences.quality, viewer, Cesium]);

  useEffect(() => {

    if (viewer.isDestroyed()) return;

    viewer.clock.shouldAnimate = playing;

    viewer.clock.multiplier = speed;
    viewer.scene.requestRender();

    return () => { if (!viewer.isDestroyed()) viewer.clock.shouldAnimate = false; };

  }, [playing, speed, viewer]);

  useEffect(() => {

    const update = () => {

      if (viewer.isDestroyed()) return;

      const time = viewer.clock.currentTime;

      const sun = Cesium.Simon1994PlanetaryPositions.computeSunPositionInEarthInertialFrame(time);

      const rotation = Cesium.Transforms.computeIcrfToCentralBodyFixedMatrix(time);

      if (!rotation) return;

      const fixed = Cesium.Matrix3.multiplyByVector(rotation, sun, new Cesium.Cartesian3());

      const origin = Cesium.Cartesian3.fromDegrees(longitude, latitude);

      const enu = Cesium.Matrix4.inverseTransformation(Cesium.Transforms.eastNorthUpToFixedFrame(origin), new Cesium.Matrix4());

      const local = Cesium.Matrix4.multiplyByPoint(enu, fixed, new Cesium.Cartesian3());

      const angles = sunAnglesFromEnu(local.x, local.y, local.z);

      viewer.scene.canvas.dataset.sceneCamera = JSON.stringify({ lng: Cesium.Math.toDegrees(viewer.camera.positionCartographic.longitude), lat: Cesium.Math.toDegrees(viewer.camera.positionCartographic.latitude), height: viewer.camera.positionCartographic.height, pitch: viewer.camera.pitch, heading: viewer.camera.heading, globe: viewer.scene.globe.show });

      setReadout({ ...angles, utc: Cesium.JulianDate.toIso8601(time), local: new Intl.DateTimeFormat("en-GB", { timeZone: preferences.timeZone, dateStyle: "medium", timeStyle: "medium" }).format(Cesium.JulianDate.toDate(time)) });

      viewer.scene.requestRender();

    };

    update(); const timer = setInterval(update, 1000);

    return () => clearInterval(timer);

  }, [viewer, Cesium, longitude, latitude, preferences.timeZone, preferences.utc]);

  const change = <K extends keyof EngineeringMapPreferences,>(key: K, value: EngineeringMapPreferences[K]) => {

    preferencesEdited.current = true;
    setSaveStatus(projectId ? "Unsaved changes" : "Session settings");

    setPreferences((current) => ({ ...current, [key]: value }));

  };

  function selectPreset(preset: ScenePreset) {
    preferencesEdited.current = true;
    setSaveStatus(projectId ? "Unsaved changes" : "Session settings");
    setPreferences((current) => scenePresetPreferences(current, preset));
    if (preset === "SUN_STUDY") setTab("Sun");
  }
  function setTime(value: string) {
    try { change("utc", localDateTimeToUtc(value, preferences.timeZone)); setPlaying(false); setError(null); }
    catch (reason) { setError(formatApiErrorMessage(reason)); }
  }
  const displayTime = localDateTimeValue(playing && readout ? readout.utc : preferences.utc, preferences.timeZone);
  const minute = Number(displayTime.slice(11, 13)) * 60 + Number(displayTime.slice(14, 16));
  return <WorkspaceMapControl side="right" fallbackClassName="absolute right-3 top-3 z-30 w-max text-xs">
    {panelContainer && createPortal(<CameraGizmo viewer={viewer} Cesium={Cesium} longitude={longitude} latitude={latitude} />, panelContainer)}
    {!projectId && <button className="flex items-center gap-2 rounded-full border border-white/15 bg-background/90 px-4 py-2.5 font-medium shadow-lg" onClick={toggle} aria-expanded={open}><Sun className="size-4 text-primary" />Scene / Sun study</button>}
    {open && createPortal(<section data-workspace-popup="scene" aria-label="Sun study" className={`${styles.panel} ${styles.scenePanel}`}>
      <header className={styles.header}><div><h2 className={styles.title}>Scene & sunlight</h2></div><button aria-label="Close sun study" className={styles.button} onClick={close}><X size={15} /></button></header>
      <div role="tablist" aria-label="Environment controls" className={styles.tabs}>{[["Scene", Layers3], ["Sun", Sun], ["Views", Camera]].map(([name, Icon]) => { const LabelIcon = Icon as typeof Sun; return <button key={String(name)} role="tab" aria-selected={tab === name} onClick={() => setTab(String(name))}><LabelIcon size={14} />{String(name)}</button>; })}</div>
      <div className={styles.body}>
        {error && <div role="alert" className={styles.notice}>{error} <button className={styles.link} onClick={() => { setError(null); setRetry((n) => n + 1); }}>Retry settings</button></div>}
        {tab === "Scene" && <>
          <div><p className={`${styles.eyebrow} mb-2`}>Look &amp; feel</p><div className={styles.grid}>{([["ENGINEERING", "Engineering", Activity], ["REALISTIC", "Realistic", Globe2]] as const).map(([value, title, Icon]) => <button key={value} aria-pressed={preferences.preset === value} onClick={() => selectPreset(value)} className={styles.preset}><Icon size={16} className="text-primary" /><span className="font-semibold">{title}</span></button>)}</div></div><div className={styles.card}><p className={styles.eyebrow}>Map layers</p>{([['terrain', 'Terrain elevation'], ['tiles3d', 'Global 3D buildings']] as const).map(([key, label]) => <label className={styles.row} key={key}><span>{label}{key === 'terrain' && <span className={`block ${styles.muted}`}>{!layers.terrain ? 'Off · flat globe' : terrainAvailable ? 'Elevation loaded' : 'Unavailable or loading'}</span>}{key === 'tiles3d' && <span className={`block ${styles.muted}`}>{!layers.tiles3d ? 'Off' : !layers.terrain ? 'Paused · enable terrain' : buildingsAvailable ? 'Buildings loaded' : 'Unavailable or loading'}</span>}</span><input type="checkbox" aria-label={label} checked={layers[key]} onChange={() => { if (key === "tiles3d" && !layers.tiles3d) useProjectStore.getState().setLayers({ terrain: true }); toggleLayer(key); }} /></label>)}</div>
          <a href="/settings/api-keys" className={styles.link}>Manage world data connection</a>
        </>}
        {tab === "Sun" && <>
          <div className={styles.hero}><div className="mb-3 flex justify-between"><p className={styles.eyebrow}>Solar position</p><span className={`${styles.badge} ${styles.good}`}>{!readout ? "Calculating" : readout.elevation > 0 ? "Daylight" : "Below horizon"}</span></div><div className={styles.metrics}><div><strong>{readout ? `${readout.elevation.toFixed(1)}°` : "—"}</strong><span className={styles.muted}>Elevation</span></div><div><strong>{readout ? `${readout.azimuth.toFixed(1)}°` : "—"}</strong><span className={styles.muted}>Azimuth · from north</span></div></div><p className={`mt-3 ${styles.muted}`}>{readout?.local ?? "Calculating sun position…"}</p></div>
          {preferences.shadows === "OFF" && <button className={styles.button} onClick={() => selectPreset("SUN_STUDY")}>Enable sun lighting & shadows</button>}
          <label className={styles.field}>Local date & time<input aria-label="Sun local date and time" type="datetime-local" className={styles.input} value={displayTime} onChange={(e) => setTime(e.target.value)} /></label>
          <label className={styles.field}><span className="flex justify-between"><span>Time of day</span><span>{displayTime.slice(11)}</span></span><input aria-label="Sun time of day" type="range" min={0} max={1439} value={minute} onChange={(e) => { const n = Number(e.target.value); setTime(`${displayTime.slice(0, 10)}T${String(Math.floor(n / 60)).padStart(2, '0')}:${String(n % 60).padStart(2, '0')}`); }} className="w-full accent-primary" /><span className={`flex justify-between ${styles.muted}`}><span>00:00</span><span>12:00</span><span>23:59</span></span></label>
          <div className="flex gap-2"><button className={styles.primary} onClick={() => { if (playing) { change("utc", Cesium.JulianDate.toIso8601(viewer.clock.currentTime)); setPlaying(false); } else { selectPreset("SUN_STUDY"); setPlaying(true); } }}>{playing ? <Pause size={14} /> : <Play size={14} />}{playing ? "Pause" : "Play day"}</button><button className={styles.button} onClick={() => { change("utc", new Date().toISOString()); setPlaying(false); }}><RotateCcw size={13} />Now</button><select aria-label="Sun playback speed" className={`${styles.input} flex-1`} value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>{[1, 60, 600, 3600].map((s) => <option key={s} value={s}>{s}× speed</option>)}</select></div>
          <label className={styles.field}>Timezone<input aria-label="Sun timezone" className={styles.input} value={zoneDraft} onChange={(e) => setZoneDraft(e.target.value)} onBlur={() => { try { new Intl.DateTimeFormat("en", { timeZone: zoneDraft }); change("timeZone", zoneDraft); setError(null); } catch { setError("Enter a timezone such as Asia/Kolkata or Europe/London."); } }} /></label>
          <div className={styles.grid}>{[["March · equinox", "03-20"], ["June · solstice", "06-21"], ["September · equinox", "09-22"], ["December · solstice", "12-21"]].map(([label, day]) => <button key={day} className={styles.button} onClick={() => setTime(`${displayTime.slice(0, 4)}-${day}T12:00`)}>{label}</button>)}</div>
          <p className={styles.muted}>Shadow coverage is partial. Terrain {terrainAvailable ? "loaded" : "unavailable"} · buildings {buildingsAvailable ? "loaded" : "unavailable"}. Trees and weather are not included.</p>
        </>}
        {tab === "Views" && <CameraViewControls viewer={viewer} Cesium={Cesium} projectId={projectId} longitude={longitude} latitude={latitude} />}
      </div>
    </section>, panelContainer ?? document.body)}
  </WorkspaceMapControl>;
}






