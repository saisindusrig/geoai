"use client";
import { Database, ChevronDown, X, ShieldCheck, RefreshCw, MapPin, Download, CheckCircle2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useWorkspacePanel } from "@/hooks/useWorkspacePanel";
import { api, formatApiErrorMessage } from "@/lib/api";
import WorkspaceMapControl from "@/components/layout/WorkspaceMapControl";
import styles from "./WorkspacePanels.module.css";

interface EvidenceItem { status: string; value?: unknown; dataset_id?: number; version_id?: number; date?: string }
interface Evidence { readiness: string; measurement_class: string; evidence: Record<string, EvidenceItem> }
interface Placement { longitude: number; latitude: number; elevation: number; offset: number; heading: number; status: string; vertical_reference?: {type?:string}; terrain_version_id?:number|null }
interface Sample { id: number; status: string; elevation: number | null; vertical_reference: Record<string, unknown> | null; failure_reason?: string; terrain_version_id: number | null }
const evidenceLabels: Record<string, [string, string]> = {
  horizontal_crs: ["Coordinate system", "Identify the survey coordinate system so data aligns with the map."],
  vertical_reference: ["Height reference", "Resolve the vertical datum and convert heights to the ellipsoid."],
  units: ["Survey units", "Confirm the source measurement units."],
  terrain: ["Project terrain", "Activate a processed terrain dataset for this site."],
  coverage: ["Site coverage", "Provide the terrain coverage boundary. Sampling checks the anchor location."],
  validation: ["Independent checkpoints", "Validate the survey against independent XYZ checkpoints."],
  spatial_backend: ["Spatial processing", "Survey processing requires the PostGIS backend."],
  authoritative_raster: ["Survey elevation raster", "Load an accepted elevation raster for authoritative ground sampling."],
};
const placementRequirements = ["horizontal_crs", "vertical_reference", "units", "terrain", "coverage", "spatial_backend", "authoritative_raster"];
function label(value: string) { return value.replaceAll("_", " ").toLowerCase(); }

export default function EngineeringEvidencePanel({ projectId, revisionId, origin, onPlacement }: { projectId: number; revisionId?: number; origin: { lng: number; lat: number; elevation_m: number; heading_deg: number }; onPlacement: (placement: Placement) => void }) {
  const [data, setData] = useState<Evidence | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { open, show, close, toggle } = useWorkspacePanel("evidence");
  const [tab, setTab] = useState("Overview");
  const [sample, setSample] = useState<Sample | null>(null);
  const [placement, setPlacement] = useState<Placement | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [provenance, setProvenance] = useState<Record<string, unknown> | null>(null);
  const [provenanceBusy, setProvenanceBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const requestId = useRef(0);
  const refresh = useCallback(async () => {
    const id = ++requestId.current;
    setLoading(true); setError(null);
    try {
      const result = await api.get<Evidence>(`/api/projects/${projectId}/engineering/evidence`);
      if (id === requestId.current) setData(result);
    } catch (reason) { if (id === requestId.current) setError(formatApiErrorMessage(reason)); }
    finally { if (id === requestId.current) setLoading(false); }
  }, [projectId]);
  useEffect(() => {
    // Refresh synchronizes the loading indicator with the external evidence request.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
    // This counter invalidates requests; it is not a DOM ref captured by the effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    return () => { requestId.current++; };
  }, [refresh]);
  useEffect(() => {
    let active = true;
    if (revisionId) void api.get<{ placement: Placement | null }>(`/api/projects/${projectId}/engineering/placements/${revisionId}`).then((result) => { if (active) setPlacement(result.placement); }).catch((reason) => { if (active) setError(formatApiErrorMessage(reason)); });
    return () => { active = false; };
  }, [projectId, revisionId]);
  useEffect(() => {
    const openEvidence = () => { setTab("Sources"); show(); void refresh(); };
    window.addEventListener("geoai:open-site-data", openEvidence);
    return () => window.removeEventListener("geoai:open-site-data", openEvidence);
  }, [show, refresh]);
  const missing = placementRequirements.filter((key) => data?.evidence[key]?.status !== "VALID");
  const validCount = data ? Object.values(data.evidence).filter((item) => item.status === "VALID").length : 0;
  const total = data ? Object.keys(data.evidence).length : 0;
  async function placeOnGround() {
    if (!revisionId || busy || missing.length || loading) return;
    setBusy(true); setError(null); setNotice(null); setProvenance(null);
    try {
      const longitude = placement?.longitude ?? origin.lng;
      const latitude = placement?.latitude ?? origin.lat;
      const heading = placement?.heading ?? origin.heading_deg;
      const result = await api.post<Sample>(`/api/projects/${projectId}/engineering/ground-samples`, { longitude, latitude });
      setSample(result);
      if (result.status !== "VALID" || result.elevation === null) throw new Error(result.failure_reason ?? "Ground elevation is unknown.");
      if (result.vertical_reference?.type !== "ELLIPSOIDAL") throw new Error("Resolve the survey height to an ellipsoidal reference before placement.");
      const accepted = await api.put<{ status: string; anchor_elevation: number }>(`/api/projects/${projectId}/engineering/placements/${revisionId}`, { placement_mode: "GROUND_RELATIVE", longitude, latitude, elevation: result.elevation, heading_deg: heading, elevation_offset: placement?.offset ?? 0, vertical_reference: result.vertical_reference, accepted_ground_sample_id: result.id });
      const next = { longitude, latitude, elevation: accepted.anchor_elevation, offset: placement?.offset ?? 0, heading, status: accepted.status,vertical_reference:result.vertical_reference,terrain_version_id:result.terrain_version_id };
      setPlacement(next); onPlacement(next); setNotice("Placement saved. The model now uses the accepted ground elevation.");
      void refresh();
    } catch (reason) { setError(formatApiErrorMessage(reason)); }
    finally { setBusy(false); }
  }
  async function loadProvenance() {
    if (!sample) return;
    setProvenanceBusy(true);
    try { setProvenance(await api.get<Record<string, unknown>>(`/api/projects/${projectId}/engineering/ground-samples/${sample.id}`)); }
    catch (reason) { setError(formatApiErrorMessage(reason)); }
    finally { setProvenanceBusy(false); }
  }
  function downloadChecklist() {
    const checklist = { project_id: projectId, required: Object.entries(evidenceLabels).map(([key, [name, action]]) => ({ name, status: data?.evidence[key]?.status ?? "UNKNOWN", action })), optional: ["Orthomosaic", "CAD alignment", "Utilities", "Site boundary", "Point cloud reference"] };
    const url = URL.createObjectURL(new Blob([JSON.stringify(checklist, null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = `project-${projectId}-survey-checklist.json`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <WorkspaceMapControl side="left" fallbackClassName="absolute left-3 top-3 z-30 w-max text-xs">
    <button className="flex items-center gap-2 rounded-full border border-white/15 bg-background/90 px-3 py-2 shadow-lg" onClick={() => { toggle(); if (!open) void refresh(); }} aria-expanded={open}><Database className="size-3.5 text-primary" />Site data<span className="workspace-site-readiness capitalize"> · {data ? label(data.readiness) : loading ? "Loading…" : "Unavailable"}</span><ChevronDown size={12} /></button>
    {open && <section aria-label="Site data readiness" className={styles.panel} style={{ left: 0 }}>
      <header className={styles.header}><div><p className={styles.eyebrow}>Site data readiness</p><h2 className={styles.title}>Data & placement</h2></div><button aria-label="Close site data" className={styles.button} onClick={close}><X size={15} /></button></header>
      <div role="tablist" aria-label="Site data sections" className={styles.tabs}>{["Overview", "Sources", "Placement"].map((name) => <button key={name} role="tab" aria-selected={tab === name} onClick={() => setTab(name)}>{name}</button>)}</div>
      <div className={styles.body}>
        {error && <p role="alert" className={styles.notice}>{error}</p>}
        {notice && <p role="status" className={styles.notice}>{notice}</p>}
        {loading && <p role="status" className={styles.muted}>Checking project evidence…</p>}
        {tab === "Overview" && <>
          <dl className={styles.card}>{[
            ["Horizontal CRS", data?.evidence.horizontal_crs?.value],
            ["Units", data?.evidence.units?.value],
            ["Vertical reference", data?.evidence.vertical_reference?.value],
            ["Terrain dataset", data?.evidence.terrain?.dataset_id],
            ["Terrain version", data?.evidence.terrain?.version_id],
            ["Survey coverage", data?.evidence.coverage?.status],
            ["Validation date", data?.evidence.validation?.date],
            ["Horizontal RMSE · m", (data?.evidence.validation?.value as Record<string, unknown> | undefined)?.horizontal_rmse_m],
            ["Vertical RMSE · m", (data?.evidence.validation?.value as Record<string, unknown> | undefined)?.vertical_rmse_m],
            ["Validation checkpoints", (data?.evidence.validation?.value as Record<string, unknown> | undefined)?.total_count],
          ].map(([name,value]) => <div key={String(name)} className={styles.row}><dt className={styles.muted}>{String(name)}</dt><dd className="max-w-[170px] break-words text-right">{value == null ? "Unavailable" : typeof value === "object" ? JSON.stringify(value) : String(value)}</dd></div>)}</dl>
          <div className={styles.card}><p className={styles.eyebrow}>Output readiness</p><div className={styles.row}><span>Engineering measurements</span><strong>{["SURVEY_READY", "ENGINEERING_READY"].includes(data?.readiness ?? "") ? "SURVEY-DERIVED" : "BLOCKED"}</strong></div><div className={styles.row}><span>Quantities</span><span>PRELIMINARY</span></div><p className={styles.muted}>{["SURVEY_READY", "ENGINEERING_READY"].includes(data?.readiness ?? "") ? "Validated survey evidence is available. Each result still requires a valid sample and matching model revision." : "Engineering measurements require validated survey terrain, resolved coordinates and independent checkpoints."}</p></div>
          <div className={styles.hero}><div className="flex items-center gap-3"><ShieldCheck size={28} className="text-primary" /><div><p className={styles.eyebrow}>Current readiness</p><p className="mt-1 text-base font-semibold capitalize">{data ? label(data.readiness) : "Awaiting evidence"}</p></div></div><div className={styles.progress} role="progressbar" aria-label="Evidence checks complete" aria-valuemin={0} aria-valuemax={total || 1} aria-valuenow={validCount}><div style={{ width: `${total ? validCount / total * 100 : 0}%` }} /></div><p className={`mt-2 ${styles.muted}`}>{validCount} of {total} checks complete</p></div>
          <p className={styles.muted}>Measurement class: <strong className="text-foreground">{data?.measurement_class ?? "Unknown"}</strong>. Visible terrain and buildings provide context; verified survey sources establish accuracy.</p>
          <div className={styles.card}><p className="mb-2 font-semibold">{missing.length ? "Next step: complete site sources" : "Ready to sample ground"}</p><p className={styles.muted}>{missing.length ? "Connect an active survey terrain with a resolved height reference and coverage for this site." : "Sample the saved model anchor and accept its ground elevation."}</p><button className={`${styles.button} mt-3 w-full`} onClick={() => setTab(missing.length ? "Sources" : "Placement")}>{missing.length ? `Review ${missing.length} placement requirements` : "Open model placement"}</button></div>
          <button className={styles.button} onClick={downloadChecklist}><Download size={14} />Download survey checklist</button>
        </>}
        {tab === "Sources" && <>
          <p className={styles.muted}>Expand a check to see its source and the action needed. Refresh after updating your survey data.</p>
          {data && Object.entries(data.evidence).map(([key, item]) => <details key={key} className={styles.details}><summary><span className="flex items-center gap-2">{item.status === "VALID" && <CheckCircle2 size={13} className="text-primary" />}{evidenceLabels[key]?.[0] ?? label(key)}</span><span className={`${styles.badge} ${item.status === "VALID" ? styles.good : ""}`}>{item.status === "VALID" ? "Ready" : label(item.status)}</span></summary><p className={`mt-3 ${styles.muted}`}>{item.status === "VALID" ? "Source verified by the project evidence service." : evidenceLabels[key]?.[1]}</p>{typeof item.value === "string" && <p className="mt-2 break-words">{item.value}</p>}{item.dataset_id != null && <p className={`mt-2 ${styles.muted}`}>Dataset {item.dataset_id} · version {item.version_id ?? "unknown"}</p>}<details className="mt-3"><summary className={styles.link}>Source details</summary><pre>{JSON.stringify(item, null, 2)}</pre></details></details>)}
          {!data && !loading && <p className={styles.notice}>Evidence is unavailable. Use Refresh below to try again.</p>}
          <button className={styles.button} onClick={downloadChecklist}><Download size={14} />Download missing-data checklist</button>
        </>}
        {tab === "Placement" && <>
          <div className={styles.card}><p className={`${styles.eyebrow} mb-2`}>Model anchor</p><div className={styles.row}><span className={styles.muted}>Latitude / longitude</span><span className="font-mono text-[11px]">{(placement?.latitude ?? origin.lat).toFixed(6)}, {(placement?.longitude ?? origin.lng).toFixed(6)}</span></div><div className={styles.row}><span className={styles.muted}>Anchor elevation</span><span>{(placement?.elevation ?? origin.elevation_m).toFixed(2)} m</span></div><div className={styles.row}><span className={styles.muted}>Heading</span><span>{(placement?.heading ?? origin.heading_deg).toFixed(1)}°</span></div><p className={`mt-2 ${styles.muted}`}>{placement ? `Accepted placement: ${label(placement.status)}` : "Model origin · ground placement not yet accepted"}</p></div>
          {!revisionId ? <p className={styles.notice}>Save a model revision before placing it on the ground.</p> : missing.length > 0 ? <div className={styles.notice}>Ground placement needs {missing.map((key) => evidenceLabels[key][0].toLowerCase()).join(", ")}.<button className={`mt-2 block ${styles.link}`} onClick={() => setTab("Sources")}>Review source requirements</button></div> : <p className={styles.muted}>Samples the current anchor, then saves its ground elevation. Geometry, heading and vertical offset are preserved.</p>}
          <button disabled={busy || loading || !revisionId || missing.length > 0} className={styles.primary} onClick={() => void placeOnGround()}><MapPin size={15} />{busy ? "Sampling & saving…" : placement ? "Resample ground & update" : "Place model on ground"}</button>
          {sample && <div className={styles.card}><p className="font-medium">{sample.status === "VALID" ? `Ground elevation: ${sample.elevation?.toFixed(2)} m` : "Ground sampling failed"}</p><p className={styles.muted}>Terrain version {sample.terrain_version_id ?? "unknown"}</p><button disabled={provenanceBusy} className={`mt-3 ${styles.link}`} onClick={() => void loadProvenance()}>{provenanceBusy ? "Loading source…" : "View sample provenance"}</button>{provenance && <dl className="mt-3">{["source", "sampled_at", "horizontal_crs", "terrain_dataset_id", "terrain_version_id", "status", "failure_reason"].filter((key) => provenance[key] != null).map((key) => <div key={key} className={styles.row}><dt className={styles.muted}>{label(key)}</dt><dd className="max-w-[60%] break-words text-right text-[10px]">{String(provenance[key])}</dd></div>)}</dl>}</div>}
        </>}
      </div>
      <footer className={styles.footer}><span>Project {projectId}{revisionId ? ` · revision ${revisionId}` : " · no saved revision"}</span><button className="flex items-center gap-1.5" disabled={loading || busy} onClick={() => void refresh()}><RefreshCw size={12} className={loading ? "animate-spin" : ""} />Refresh</button></footer>
    </section>}
  </WorkspaceMapControl>;
}
