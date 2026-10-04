"use client";

import dynamic from "next/dynamic";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowLeftRight,
  Boxes,
  CheckCircle2,
  CircleAlert,
  Eye,
  EyeOff,
  LocateFixed,
  MapPinned,
  Minus,
  MoveRight,
  Pencil,
  Plus,
  RotateCcw,
  RotateCw,
  Ruler,
  Save,
  ShieldCheck,
  Sparkles,
  Undo2,
  X,
} from "lucide-react";
import SiteMap, { type SiteMapEndpoint } from "./SiteMap";
import type { ConstructionMapPlacement } from "./ConstructionMapOverlay";
import type { GeoPoint, SiteContext } from "@/lib/civicspan";
import { api, getAuthToken } from "@/lib/api";
import { redirectDemoGuestToRegistration } from "@/lib/auth-routes";
import { saveLocalSandboxDraft } from "@/lib/local-sandbox";
import type { Project } from "@/lib/types";
import { useProjectStore } from "@/stores/projectStore";
import {
  CONSTRUCTION_LABELS,
  CONSTRUCTION_TYPES,
  type ConstructionPlan,
  type ConstructionStage,
  type ConstructionType,
  TEMPLATE_PROMPTS,
  offlineConstructionPlan,
  spanMeters,
} from "@/lib/construction";

const ConstructionScene = dynamic(() => import("./ConstructionScene"), {
  ssr: false,
  loading: () => (
    <div className="grid h-full place-items-center text-sm text-muted-foreground">
      Loading 3D preview…
    </div>
  ),
});
const DEFAULT_START = { lat: 18.525, lng: 73.852 };
const DEFAULT_END = { lat: 18.525, lng: 73.8525 };
const STAGES: ConstructionStage[] = [
  "site",
  "foundation",
  "structure",
  "finish",
];
const DEFAULT_MAP_PLACEMENT: ConstructionMapPlacement = {
  rotationDeg: 0,
  offsetAcrossM: 0,
  scale: 1,
  elevationM: 0,
};

function savedEndpoints(project?: Project) {
  const coords =
    project?.alignment_geojson?.type === "LineString"
      ? project.alignment_geojson.coordinates
      : null;
  if (
    Array.isArray(coords) &&
    coords.length >= 2 &&
    Array.isArray(coords[0]) &&
    Array.isArray(coords[coords.length - 1])
  ) {
    const first = coords[0];
    const last = coords[coords.length - 1];
    if (
      typeof first[0] === "number" &&
      typeof first[1] === "number" &&
      typeof last[0] === "number" &&
      typeof last[1] === "number"
    )
      return {
        start: { lng: first[0], lat: first[1] },
        end: { lng: last[0], lat: last[1] },
      };
  }
  return { start: DEFAULT_START, end: DEFAULT_END };
}

function ConstructionStudioContent({ project }: { project?: Project }) {
  const router = useRouter();
  const params = useSearchParams();
  const requestedType = params.get("template") ?? params.get("type");
  const validType: ConstructionType = CONSTRUCTION_TYPES.includes(
    requestedType as ConstructionType,
  )
    ? (requestedType as ConstructionType)
    : (project?.project_type as ConstructionType) || "bridge";
  const endpoints = savedEndpoints(project);
  const [projectType, setProjectType] = useState<ConstructionType>(validType);
  const [start, setStart] = useState<GeoPoint>(endpoints.start);
  const [end, setEnd] = useState<GeoPoint>(endpoints.end);
  const [name, setName] = useState(project?.name ?? "");
  const [prompt, setPrompt] = useState(() => TEMPLATE_PROMPTS[validType]);
  const [plan, setPlan] = useState<ConstructionPlan | null>(null);
  const [stage, setStage] = useState<ConstructionStage>("finish");
  const [crossing, setCrossing] = useState<SiteContext["crossing"]>("waterway");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [aiOpen, setAiOpen] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [activeEndpoint, setActiveEndpoint] =
    useState<SiteMapEndpoint>("start");
  const [fitRequest, setFitRequest] = useState(0);
  const [mapModelVisible, setMapModelVisible] = useState(true);
  const [mapPlacement, setMapPlacement] = useState<ConstructionMapPlacement>(
    DEFAULT_MAP_PLACEMENT,
  );
  const isGuestDemo = params.get("demo") === "1" && !getAuthToken();
  const isLocalSandbox = params.get("local") === "1";
  const site = useMemo<SiteContext>(
    () => ({
      start,
      end,
      crossing,
      terrain_slope_pct: 3,
      nearby_buildings: 4,
      nearby_roads: 2,
    }),
    [start, end, crossing],
  );
  const setPoints = useCallback((nextStart: GeoPoint, nextEnd: GeoPoint) => {
    setStart(nextStart);
    setEnd(nextEnd);
    setPlan(null);
    setMessage(null);
  }, []);
  const changeType = (type: ConstructionType) => {
    setProjectType(type);
    setPrompt(TEMPLATE_PROMPTS[type]);
    setPlan(null);
    setMessage(null);
  };

  async function generate() {
    if (isLocalSandbox) {
      setPlan(offlineConstructionPlan(site, prompt, projectType));
      setStage("finish");
      setMessage(
        "Local procedural preview updated. No GeoAI, Nebius, or backend API request was made.",
      );
      return;
    }
    if (
      params.get("demo") === "1" &&
      redirectDemoGuestToRegistration(
        `${window.location.pathname}${window.location.search}`,
      )
    ) {
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/geoai/concept`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(getAuthToken()
              ? { Authorization: `Bearer ${getAuthToken()}` }
              : {}),
          },
          body: JSON.stringify({
            project_type: projectType,
            request: prompt,
            site,
            current_spec: plan?.spec ?? null,
          }),
        },
      );
      if (!response.ok) throw new Error("Planner unavailable");
      setPlan((await response.json()) as ConstructionPlan);
      setStage("finish");
    } catch {
      setPlan(offlineConstructionPlan(site, prompt, projectType));
      setStage("finish");
      setMessage(
        "Local concept preview shown. Configure Nebius Token Factory to plan with Nemotron.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function save() {
    if (isLocalSandbox) {
      const localProject = saveLocalSandboxDraft({
        name: name.trim() || "Local 3D Sandbox",
        projectType,
        crossing,
        start,
        end,
      });
      useProjectStore.getState().setProject(localProject);
      setName(localProject.name);
      setMessage(
        "Saved in this browser only. Nothing was sent to the GeoAI backend or added to your dashboard.",
      );
      return;
    }
    if (
      isGuestDemo &&
      redirectDemoGuestToRegistration(
        `${window.location.pathname}${window.location.search}`,
      )
    ) {
      return;
    }
    if (!name.trim()) {
      setMessage("Give this concept a project name before saving it.");
      return;
    }
    setSaving(true);
    setMessage(null);
    const payload = {
      name: name.trim(),
      project_type: projectType,
      units: "metric",
      location_name: `${crossing.replace("unknown", "map-selected")} site`,
      center_lat: Number(((start.lat + end.lat) / 2).toFixed(6)),
      center_lng: Number(((start.lng + end.lng) / 2).toFixed(6)),
      boundary_geojson: null,
      alignment_geojson: {
        type: "LineString",
        coordinates: [
          [start.lng, start.lat],
          [end.lng, end.lat],
        ],
      },
    };
    try {
      if (project) {
        await api.put(`/api/projects/${project.id}`, payload);
        setMessage("Saved workspace changes.");
      } else {
        await api.post<Project>("/api/projects", payload);
        router.push("/dashboard");
      }
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Could not save this project.",
      );
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    const onHeaderSave = () => void save();
    window.addEventListener("geoai:save-project", onHeaderSave);
    return () => window.removeEventListener("geoai:save-project", onHeaderSave);
  });

  const activePlan = plan ?? offlineConstructionPlan(site, prompt, projectType);
  const dummyBridgeModelUrl =
    isLocalSandbox &&
    (projectType === "bridge" || projectType === "flyover")
      ? "/models/dummy-arch-bridge.glb"
      : undefined;
  return (
    <div className="min-h-screen min-w-[1280px] bg-[#07100f] text-foreground">
      <header className="flex min-h-[68px] items-center justify-between gap-5 border-b border-white/10 bg-[#08100f]/95 px-6 shadow-[0_12px_32px_rgba(0,0,0,0.22)]">
        <div className="flex min-w-0 items-center gap-4">
          <div className="grid size-9 shrink-0 place-items-center rounded-xl border border-emerald-300/25 bg-emerald-300/10 text-sm font-black tracking-tighter text-emerald-200">S</div>
          <div className="min-w-0 border-l border-white/10 pl-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-200/80">
            Sitegeo AI · Design workspace
          </p>
          <div className="mt-1 flex items-center gap-1.5">
            {editingName ? (
              <input
                autoFocus
                value={name}
                onChange={(event) => setName(event.target.value)}
                onBlur={() => setEditingName(false)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") setEditingName(false);
                  if (event.key === "Escape") {
                    setName(project?.name ?? "");
                    setEditingName(false);
                  }
                }}
                aria-label="Project name"
                className="h-8 w-72 rounded-lg border border-primary/50 bg-background px-2 text-lg font-semibold outline-none"
              />
            ) : (
              <h1 className="truncate text-lg font-semibold">
                {name || "Unsaved construction concept"}
              </h1>
            )}
            <button
              type="button"
              onClick={() => setEditingName(true)}
              aria-label="Edit project name"
              title="Edit project name"
              className="rounded-md p-1 text-muted-foreground transition hover:bg-surface-hover hover:text-foreground"
            >
              <Pencil className="size-3.5" />
            </button>
          </div>
          <label className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
            Active asset
            <select
              value={projectType}
              onChange={(event) =>
                changeType(event.target.value as ConstructionType)
              }
              className="h-7 rounded-md border border-border bg-background px-2 text-xs font-medium text-foreground outline-none focus:border-primary"
            >
              <option value="bridge">Bridge</option>
              <option value="flyover">Flyover</option>
              <option value="building">Building</option>
              <option value="road">Road</option>
              <option value="pipeline">Pipeline</option>
              <option value="dam">Dam</option>
            </select>
          </label>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <div className="rounded-lg border border-emerald-300/15 bg-emerald-300/5 px-3 py-1.5 text-right">
            <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Workspace status</p>
            <p className="mt-0.5 flex items-center gap-1.5 text-[11px] font-medium text-emerald-100"><span className="size-1.5 rounded-full bg-emerald-300" /> Synced locally</p>
          </div>
          <ShieldCheck className="size-5 text-emerald-200/80" aria-label="Concept workspace" />
        </div>
      </header>
      <div
        className="flex min-h-12 items-center gap-2 overflow-x-auto border-b border-white/10 bg-[#0b1614] px-5 py-1.5"
        role="toolbar"
        aria-label="Construction workspace tools"
      >
        <span className="shrink-0 pr-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-100/65">
          01 · Site geometry
        </span>
        {(["start", "end"] as SiteMapEndpoint[]).map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setActiveEndpoint(item)}
            aria-pressed={activeEndpoint === item}
            className={`flex h-8 shrink-0 items-center gap-1.5 rounded-lg border px-2.5 text-xs font-semibold transition ${activeEndpoint === item ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"}`}
          >
            <MapPinned className="size-3.5" />
            Set {item}
          </button>
        ))}
        <button
          type="button"
          onClick={() => {
            setStart(end);
            setEnd(start);
            setPlan(null);
            setMessage(null);
          }}
          className="flex h-8 shrink-0 items-center gap-1.5 rounded-lg border border-border bg-background px-2.5 text-xs font-semibold text-foreground-secondary transition hover:border-primary/40 hover:bg-surface-hover"
        >
          <ArrowLeftRight className="size-3.5" />
          Swap
        </button>
        <button
          type="button"
          onClick={() => setFitRequest((value) => value + 1)}
          className="flex h-8 shrink-0 items-center gap-1.5 rounded-lg border border-border bg-background px-2.5 text-xs font-semibold text-foreground-secondary transition hover:border-primary/40 hover:bg-surface-hover"
        >
          <LocateFixed className="size-3.5" />
          Fit site
        </button>
        <div className="mx-1 h-6 w-px shrink-0 bg-border" aria-hidden />
        <span className="flex h-8 shrink-0 items-center gap-1.5 rounded-lg border border-border bg-background px-2.5 font-mono text-xs text-foreground">
          <Ruler className="size-3.5 text-primary" />
          {spanMeters(start, end).toFixed(1)} m
        </span>
        <div className="mx-1 h-6 w-px shrink-0 bg-border" aria-hidden />
        <span className="shrink-0 pr-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-100/65">
          02 · Model placement
        </span>
        <button
          type="button"
          onClick={() => setMapModelVisible((visible) => !visible)}
          aria-pressed={mapModelVisible}
          title="Show or hide the 3D design on the map"
          className={`flex h-8 shrink-0 items-center gap-1.5 rounded-lg border px-2.5 text-xs font-semibold transition ${mapModelVisible ? "border-primary/50 bg-primary/15 text-primary" : "border-border bg-background text-muted-foreground"}`}
        >
          {mapModelVisible ? <Eye className="size-3.5" /> : <EyeOff className="size-3.5" />}
          Map model
        </button>
        <button
          type="button"
          onClick={() =>
            setMapPlacement((value) => ({
              ...value,
              rotationDeg: value.rotationDeg - 15,
            }))
          }
          title="Rotate design 15 degrees counter-clockwise"
          aria-label="Rotate design left"
          className="grid size-8 shrink-0 place-items-center rounded-lg border border-border bg-background text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"
        >
          <RotateCcw className="size-3.5" />
        </button>
        <button
          type="button"
          onClick={() =>
            setMapPlacement((value) => ({
              ...value,
              rotationDeg: value.rotationDeg + 15,
            }))
          }
          title="Rotate design 15 degrees clockwise"
          aria-label="Rotate design right"
          className="grid size-8 shrink-0 place-items-center rounded-lg border border-border bg-background text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"
        >
          <RotateCw className="size-3.5" />
        </button>
        <button
          type="button"
          onClick={() =>
            setMapPlacement((value) => ({
              ...value,
              offsetAcrossM: value.offsetAcrossM - 5,
            }))
          }
          title="Move design left by 5 metres"
          className="flex h-8 shrink-0 items-center gap-1 rounded-lg border border-border bg-background px-2 text-[11px] font-semibold text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"
        >
          <ArrowLeftRight className="size-3.5" /> −5m
        </button>
        <button
          type="button"
          onClick={() =>
            setMapPlacement((value) => ({
              ...value,
              offsetAcrossM: value.offsetAcrossM + 5,
            }))
          }
          title="Move design right by 5 metres"
          className="flex h-8 shrink-0 items-center gap-1 rounded-lg border border-border bg-background px-2 text-[11px] font-semibold text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"
        >
          <ArrowLeftRight className="size-3.5" /> +5m
        </button>
        <button
          type="button"
          onClick={() =>
            setMapPlacement((value) => ({
              ...value,
              scale: Math.max(0.5, Number((value.scale - 0.1).toFixed(1))),
            }))
          }
          title="Scale design down"
          aria-label="Scale design down"
          className="grid size-8 shrink-0 place-items-center rounded-lg border border-border bg-background text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"
        >
          <Minus className="size-3.5" />
        </button>
        <span className="w-9 shrink-0 text-center font-mono text-[10px] text-muted-foreground">
          {Math.round(mapPlacement.scale * 100)}%
        </span>
        <button
          type="button"
          onClick={() =>
            setMapPlacement((value) => ({
              ...value,
              scale: Math.min(2, Number((value.scale + 0.1).toFixed(1))),
            }))
          }
          title="Scale design up"
          aria-label="Scale design up"
          className="grid size-8 shrink-0 place-items-center rounded-lg border border-border bg-background text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"
        >
          <Plus className="size-3.5" />
        </button>
        <button
          type="button"
          onClick={() => setMapPlacement(DEFAULT_MAP_PLACEMENT)}
          title="Reset 3D placement"
          aria-label="Reset 3D placement"
          className="grid size-8 shrink-0 place-items-center rounded-lg border border-border bg-background text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"
        >
          <Undo2 className="size-3.5" />
        </button>
        <div className="flex-1" />
        <button
          type="button"
          onClick={() => void generate()}
          disabled={loading}
          className="flex h-8 shrink-0 items-center gap-1.5 rounded-lg bg-primary px-3 text-xs font-semibold text-primary-foreground transition hover:brightness-105 disabled:opacity-60"
        >
          <Sparkles className="size-3.5" />
          {loading ? "Generating…" : "Generate"}
        </button>
        {!isGuestDemo && (
          <button
            type="button"
            onClick={() => void save()}
            disabled={saving}
            className="flex h-8 shrink-0 items-center gap-1.5 rounded-lg border border-primary/35 bg-primary/10 px-3 text-xs font-semibold text-foreground transition hover:bg-primary/15 disabled:opacity-60"
          >
            <Save className="size-3.5" />
            {saving ? "Saving…" : isLocalSandbox ? "Save locally" : "Save"}
          </button>
        )}
        <button
          type="button"
          onClick={() => setAiOpen((open) => !open)}
          aria-pressed={aiOpen}
          className={`flex h-8 shrink-0 items-center gap-1.5 rounded-lg border px-3 text-xs font-semibold transition ${aiOpen ? "border-primary bg-primary/15 text-primary" : "border-border bg-background text-foreground-secondary hover:border-primary/40 hover:bg-surface-hover"}`}
        >
          <Sparkles className="size-3.5" />
          Planner
        </button>
      </div>
      <main
        className={`relative grid min-h-[calc(100vh-120px)] ${aiOpen ? "grid-cols-[minmax(320px,0.72fr)_minmax(540px,1.28fr)_minmax(360px,0.8fr)]" : "grid-cols-[minmax(320px,0.72fr)_minmax(680px,1.55fr)]"}`}
      >
        <section className="border-r border-white/10 bg-[#0b1513] p-5">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-200/85">
              01 · Site context
            </p>
            <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-2 py-0.5 text-[9px] font-semibold text-emerald-100">LIVE</span>
          </div>
          <h2 className="mt-1 text-xl font-semibold">
            Place the construction context
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Set endpoints on the map. They guide the visual context and never
            replace a survey.
          </p>
          <div className="mt-5 overflow-hidden rounded-xl border border-white/15 shadow-[0_16px_34px_rgba(0,0,0,0.28)]">
            <SiteMap
              start={start}
              end={end}
              onPointsChange={setPoints}
              activeEndpoint={activeEndpoint}
              onActiveEndpointChange={setActiveEndpoint}
              fitRequest={fitRequest}
              constructionSpec={activePlan.spec}
              constructionStage={stage}
              constructionPlacement={mapPlacement}
              showConstruction={mapModelVisible}
              constructionModelUrl={dummyBridgeModelUrl}
            />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-white/10 bg-black/15 p-3">
              <MapPinned className="size-4 text-emerald-200" />
              <p className="mt-2 text-xs text-muted-foreground">
                Map context span
              </p>
              <p className="mt-1 font-mono text-lg">
                {spanMeters(start, end).toFixed(1)} m
              </p>
            </div>
            <label className="rounded-xl border border-white/10 bg-black/15 p-3 text-xs text-muted-foreground">
              Site type
              <select
                value={crossing}
                onChange={(event) =>
                  setCrossing(event.target.value as SiteContext["crossing"])
                }
                className="mt-2 w-full bg-transparent text-sm font-medium text-foreground outline-none"
              >
                <option value="waterway">Waterway</option>
                <option value="road">Road crossing</option>
                <option value="terrain">Terrain</option>
                <option value="unknown">Unknown</option>
              </select>
            </label>
          </div>
        </section>
        <section className="border-r border-white/10 bg-[#07100f] p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-200/85">
                02 · Design model
              </p>
              <h2 className="mt-1 text-xl font-semibold">
                Procedural construction preview
              </h2>
            </div>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-emerald-50/75">
              {CONSTRUCTION_LABELS[projectType]}
            </span>
          </div>
          <div className="relative mt-5 h-[calc(100vh-265px)] overflow-hidden rounded-xl border border-emerald-300/15 bg-background-elevated shadow-[0_18px_38px_rgba(0,0,0,0.35)]">
            <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-lg border border-white/10 bg-[#07100f]/80 px-3 py-2 backdrop-blur-md">
              <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-emerald-100/70">Concept preview</p>
              <p className="mt-0.5 text-[11px] text-foreground">LOD 200 · procedural mesh</p>
            </div>
            <ConstructionScene
              spec={activePlan.spec}
              stage={stage}
              modelUrl={dummyBridgeModelUrl}
            />
          </div>
          <div className="mt-4 flex items-center gap-2">
            <span className="mr-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Phase</span>
            {STAGES.map((item) => (
              <button
                type="button"
                key={item}
                onClick={() => setStage(item)}
                className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${stage === item ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card text-muted-foreground hover:border-primary/40"}`}
              >
                {item}
              </button>
            ))}
          </div>
        </section>
        {!aiOpen && (
          <div className="absolute right-6 top-5 z-10 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setAiOpen(true)}
              aria-label="Open GeoAI planner"
              title="Try GeoAI"
              className="grid size-12 place-items-center rounded-full border border-primary/45 bg-primary text-primary-foreground shadow-[var(--shadow-md)] transition hover:scale-105"
            >
              <Sparkles className="size-5" />
            </button>
            <span className="rounded-full border border-border bg-card px-3 py-1.5 text-xs font-semibold text-foreground shadow-[var(--shadow-sm)]">
              Try GeoAI
            </span>
          </div>
        )}
        {aiOpen && (
          <section className="overflow-y-auto bg-[#0b1513] p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-200/85">
                  03 · GeoAI planner
                </p>
                <h2 className="mt-1 text-xl font-semibold">Try an idea</h2>
              </div>
              <button
                type="button"
                onClick={() => setAiOpen(false)}
                aria-label="Close GeoAI planner"
                title="Close AI planner"
                className="rounded-lg p-2 text-muted-foreground transition hover:bg-surface-hover hover:text-foreground"
              >
                <X className="size-4" />
              </button>
            </div>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              Describe the change you want to explore. GeoAI will create a constrained conceptual preview.
            </p>
            <div className="mt-4 rounded-xl border border-white/10 bg-black/15 p-3">
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-2 font-medium text-foreground"><Boxes className="size-3.5 text-emerald-200" /> Generated model</span>
                <span className="text-emerald-200">Ready</span>
              </div>
              <div className="mt-3 space-y-2 text-[10px] text-muted-foreground">
                {["Deck and safety barriers", `${activePlan.spec.supports} support assemblies`, "Foundation envelope"].map((layer) => <div key={layer} className="flex items-center justify-between"><span>{layer}</span><Eye className="size-3 text-emerald-100/70" /></div>)}
              </div>
            </div>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            className="mt-3 min-h-28 w-full resize-none rounded-xl border border-border bg-background p-3 text-sm leading-6 text-foreground"
          />
            <button
            type="button"
            onClick={generate}
            disabled={loading}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground disabled:opacity-70"
          >
            <Sparkles className="size-4" />
            {loading ? "Nemotron is planning…" : "Generate concept"}
            <MoveRight className="size-4" />
            </button>
          {!isGuestDemo && (
            <button
            type="button"
            onClick={save}
            disabled={saving}
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl border border-primary/35 bg-primary/10 px-4 py-3 text-sm font-semibold text-foreground-secondary disabled:opacity-70"
          >
            <Save className="size-4" />
              {saving
                ? "Saving…"
                : isLocalSandbox
                  ? "Save locally"
                  : project
                    ? "Save workspace"
                    : "Save to dashboard"}
            </button>
          )}
          {message && (
            <div className="mt-3 flex gap-2 rounded-xl border border-warning/25 bg-warning/10 p-3 text-xs leading-5 text-warning-text">
              <CircleAlert className="size-4 shrink-0" />
              {message}
            </div>
          )}
            <div className="mt-5 rounded-2xl border border-primary/15 bg-primary/5 p-4">
            <p className="font-medium text-foreground">{activePlan.summary}</p>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              {activePlan.explanation}
            </p>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-lg bg-card p-2">
                <p className="text-muted-foreground">Width</p>
                <p className="mt-1 font-mono">{activePlan.spec.width_m}m</p>
              </div>
              <div className="rounded-lg bg-card p-2">
                <p className="text-muted-foreground">Length</p>
                <p className="mt-1 font-mono">{activePlan.spec.length_m}m</p>
              </div>
              <div className="rounded-lg bg-card p-2">
                <p className="text-muted-foreground">Height</p>
                <p className="mt-1 font-mono">{activePlan.spec.height_m}m</p>
              </div>
            </div>
            {activePlan.assumptions.map((item) => (
              <p
                key={item}
                className="mt-3 flex gap-2 text-xs leading-5 text-muted-foreground"
              >
                <CheckCircle2 className="size-3.5 shrink-0 text-primary" />
                {item}
              </p>
            ))}
            </div>
            <p className="mt-5 text-[11px] leading-5 text-muted-foreground">
            Conceptual visualization only. It is not a structural design,
            survey, cost estimate, permit application, or construction-ready
            plan.
          </p>
          </section>
        )}
      </main>
    </div>
  );
}

export default function ConstructionStudio(props: { project?: Project }) {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-screen place-items-center bg-background text-sm text-muted-foreground">
          Loading workspace…
        </div>
      }
    >
      <ConstructionStudioContent {...props} />
    </Suspense>
  );
}
