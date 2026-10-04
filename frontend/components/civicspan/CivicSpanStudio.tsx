"use client";

import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useMemo, useState } from "react";
import {
  Bot,
  CheckCircle2,
  CircleAlert,
  MapPin,
  MoveRight,
  Route,
  Save,
  Sparkles,
  WandSparkles,
} from "lucide-react";
import {
  type BridgePlan,
  type GeoPoint,
  type SiteContext,
  STAGES,
  offlinePlan,
  spanMeters,
} from "@/lib/civicspan";
import { api, getAuthToken } from "@/lib/api";
import { redirectDemoGuestToRegistration } from "@/lib/auth-routes";
import type { Project } from "@/lib/types";

const SiteMap = dynamic(() => import("./SiteMap"), {
  ssr: false,
  loading: () => (
    <div className="grid h-full place-items-center bg-slate-950 text-sm text-slate-400">
      Loading map context…
    </div>
  ),
});
const BridgeScene = dynamic(() => import("./BridgeScene"), {
  ssr: false,
  loading: () => (
    <div className="grid h-full place-items-center bg-slate-950 text-sm text-slate-400">
      Loading 3D scene…
    </div>
  ),
});
const DEFAULT_START = { lat: 18.525, lng: 73.852 };
const DEFAULT_END = { lat: 18.525, lng: 73.8525 };
const DEFAULT_PROMPT =
  "Build a 4 meter wide pedestrian bridge between these points with concrete foundations, two concrete pillars, steel truss structure, concrete deck, and railings.";
const TEMPLATE_PROMPTS: Record<string, string> = {
  pedestrian: DEFAULT_PROMPT,
  river:
    "Create a 4 meter wide steel truss pedestrian bridge across this waterway with concrete foundations, supports, railings, and a durable walking deck.",
  park: "Create a compact, accessible pedestrian bridge that connects these park paths with a low-profile steel structure, railings, and a welcoming walking deck.",
};
const stageLabel = (stage: string) =>
  stage === "steel"
    ? "Steel structure"
    : stage[0].toUpperCase() + stage.slice(1);

function projectEndpoints(project?: Project) {
  const coordinates =
    project?.alignment_geojson?.type === "LineString"
      ? project.alignment_geojson.coordinates
      : null;
  if (Array.isArray(coordinates) && coordinates.length >= 2) {
    const first = coordinates[0];
    const last = coordinates[coordinates.length - 1];
    if (
      Array.isArray(first) &&
      Array.isArray(last) &&
      typeof first[0] === "number" &&
      typeof first[1] === "number" &&
      typeof last[0] === "number" &&
      typeof last[1] === "number"
    ) {
      return {
        start: { lng: first[0], lat: first[1] },
        end: { lng: last[0], lat: last[1] },
      };
    }
  }
  return { start: DEFAULT_START, end: DEFAULT_END };
}

type GeoAIStudioProps = { project?: Project };

function GeoAIStudioContent({ project }: GeoAIStudioProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialPoints = projectEndpoints(project);
  const [start, setStart] = useState<GeoPoint>(initialPoints.start);
  const [end, setEnd] = useState<GeoPoint>(initialPoints.end);
  const [name, setName] = useState(project?.name ?? "");
  const [prompt, setPrompt] = useState(
    () =>
      TEMPLATE_PROMPTS[searchParams.get("template") ?? ""] ?? DEFAULT_PROMPT,
  );
  const [plan, setPlan] = useState<BridgePlan | null>(null);
  const [stage, setStage] = useState<(typeof STAGES)[number]>("finished");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [crossing, setCrossing] = useState<SiteContext["crossing"]>("waterway");
  const site = useMemo<SiteContext>(
    () => ({
      start,
      end,
      crossing,
      terrain_slope_pct: 3.1,
      nearby_buildings: 4,
      nearby_roads: 2,
    }),
    [start, end, crossing],
  );
  const span = spanMeters(start, end);
  const setPoints = useCallback((nextStart: GeoPoint, nextEnd: GeoPoint) => {
    setStart(nextStart);
    setEnd(nextEnd);
    setPlan(null);
    setError(null);
    setSaveMessage(null);
  }, []);

  async function generate() {
    if (
      searchParams.get("demo") === "1" &&
      redirectDemoGuestToRegistration(
        `${window.location.pathname}${window.location.search}`,
      )
    ) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/geoai/plan`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(getAuthToken()
              ? { Authorization: `Bearer ${getAuthToken()}` }
              : {}),
          },
          body: JSON.stringify({
            prompt,
            site,
            current_spec: plan?.spec ?? null,
          }),
        },
      );
      if (!response.ok) throw new Error("The planner is unavailable.");
      setPlan((await response.json()) as BridgePlan);
      setStage("finished");
    } catch {
      setPlan(offlinePlan(site, prompt));
      setStage("finished");
      setError(
        "API unavailable: showing a local preview. Start the FastAPI backend and configure NEBIUS_API_KEY for the live Nemotron planner.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function saveProject() {
    if (!name.trim()) {
      setError("Give this bridge concept a project name before saving it.");
      return;
    }
    setSaving(true);
    setError(null);
    setSaveMessage(null);
    const payload = {
      name: name.trim(),
      project_type: "bridge",
      units: "metric",
      location_name: `${crossing.replace("unknown", "map-selected")} bridge crossing`,
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
        setSaveMessage("Saved changes to this project.");
      } else {
        await api.post<Project>("/api/projects", payload);
        router.push("/dashboard");
      }
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "Could not save this project. Start the backend and sign in, then try again.",
      );
    } finally {
      setSaving(false);
    }
  }

  const spec = plan?.spec ?? offlinePlan(site, prompt).spec;
  return (
    <div className="min-h-screen min-w-[1280px] bg-background text-foreground">
      <header className="flex items-center justify-between gap-4 border-b border-border bg-background/95 px-5 py-3 backdrop-blur">
        <div className="flex min-w-0 items-center gap-3">
          <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground">
            <Route className="size-5" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate font-semibold tracking-tight">
              {project?.name || "GeoAI"}
            </h1>
            <p className="truncate text-xs text-muted-foreground">
              {project
                ? "Saved bridge concept workspace"
                : "Unsaved site-aware bridge concept"}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="hidden rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground sm:inline">
            {project ? "Saved project" : "Draft"}
          </span>
          <span className="rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs text-foreground-secondary">
            Nebius × NVIDIA Nemotron
          </span>
        </div>
      </header>
      <main className="grid min-h-[calc(100vh-65px)] grid-cols-[minmax(330px,0.8fr)_minmax(520px,1.2fr)_minmax(420px,1fr)]">
        <section className="border-b-0 border-r border-border bg-background-secondary p-5">
          <div className="mb-5">
            <p className="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
              01 · Site context
            </p>
            <h2 className="text-xl font-semibold">Place a crossing</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Choose the endpoint mode, then click the map or use your location.
              GeoAI uses the selected location as visual context—not survey
              data.
            </p>
          </div>
          <div className="overflow-hidden rounded-2xl border border-white/10 shadow-2xl">
            <SiteMap start={start} end={end} onPointsChange={setPoints} />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-xl border border-border bg-card p-3">
              <MapPin className="mb-2 size-4 text-primary" />
              <p className="text-xs text-muted-foreground">Map-derived span</p>
              <p className="mt-1 font-mono text-lg">{span.toFixed(1)} m</p>
              <p className="mt-2 text-[10px] text-muted-foreground">
                Start {start.lat.toFixed(5)}, {start.lng.toFixed(5)}
                <br />
                End {end.lat.toFixed(5)}, {end.lng.toFixed(5)}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card p-3">
              <Route className="mb-2 size-4 text-primary" />
              <label
                className="text-xs text-muted-foreground"
                htmlFor="crossing-type"
              >
                Site classification
              </label>
              <select
                id="crossing-type"
                value={crossing}
                onChange={(event) => {
                  setCrossing(event.target.value as SiteContext["crossing"]);
                  setPlan(null);
                }}
                className="mt-1 w-full rounded-lg border border-border bg-background px-2 py-1.5 text-sm font-medium text-foreground outline-none focus:ring-2 focus:ring-primary/40"
              >
                <option value="waterway">Waterway crossing</option>
                <option value="road">Road crossing</option>
                <option value="terrain">Terrain crossing</option>
                <option value="unknown">Unknown context</option>
              </select>
              <p className="mt-2 text-[10px] leading-4 text-muted-foreground">
                This setting is sent to Nemotron with your selected endpoints.
              </p>
            </div>
          </div>
        </section>
        <section className="border-b-0 border-r border-border bg-background p-5">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
                02 · Concept scene
              </p>
              <h2 className="text-xl font-semibold">
                Editable procedural bridge
              </h2>
            </div>
            <span className="rounded-full bg-card px-3 py-1 text-xs text-muted-foreground">
              {spec.structure_type.replace("_", " ")}
            </span>
          </div>
          <div className="h-[calc(100vh-245px)] overflow-hidden rounded-2xl border border-border bg-background-elevated shadow-2xl">
            <BridgeScene spec={spec} stage={stage} />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {STAGES.map((item, index) => (
              <button
                type="button"
                key={item}
                onClick={() => setStage(item)}
                className={`rounded-full border px-3 py-1.5 text-xs transition ${stage === item ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card text-muted-foreground hover:border-primary/40"}`}
              >
                <span className="mr-1.5 opacity-70">{index + 1}</span>
                {stageLabel(item)}
              </button>
            ))}
          </div>
        </section>
        <section className="bg-background-secondary p-5">
          <p className="mb-1 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
            03 · Nemotron planner
          </p>
          <h2 className="text-xl font-semibold">Describe the bridge</h2>
          <label
            className="mt-4 block text-xs font-medium text-muted-foreground"
            htmlFor="project-name"
          >
            Project name
            <input
              id="project-name"
              value={name}
              onChange={(event) => {
                setName(event.target.value);
                setSaveMessage(null);
              }}
              placeholder="e.g. Riverside footbridge concept"
              className="mt-1.5 h-11 w-full rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none ring-primary/40 placeholder:text-muted-foreground focus:ring-2"
            />
          </label>
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            className="mt-4 min-h-32 w-full resize-none rounded-2xl border border-border bg-background p-4 text-sm leading-6 text-foreground outline-none ring-primary/40 placeholder:text-muted-foreground focus:ring-2"
            aria-label="Bridge request"
          />
          <button
            type="button"
            onClick={generate}
            disabled={loading}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition hover:bg-primary-hover disabled:cursor-wait disabled:opacity-70"
          >
            <Sparkles className="size-4" />
            {loading
              ? "Nemotron is planning…"
              : plan
                ? "Apply requested modification"
                : "Generate bridge concept"}
            <MoveRight className="size-4" />
          </button>
          <button
            type="button"
            onClick={saveProject}
            disabled={saving}
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl border border-primary/35 bg-primary/10 px-4 py-3 text-sm font-semibold text-foreground-secondary transition hover:bg-primary/20 disabled:cursor-wait disabled:opacity-70"
          >
            <Save className="size-4" />
            {saving
              ? "Saving project…"
              : project
                ? "Save workspace changes"
                : "Save to dashboard"}
          </button>
          {error && (
            <div className="mt-3 flex gap-2 rounded-xl border border-amber-300/20 bg-amber-300/10 p-3 text-xs leading-5 text-amber-100">
              <CircleAlert className="mt-0.5 size-4 shrink-0" />
              {error}
            </div>
          )}
          {saveMessage && (
            <div className="mt-3 rounded-xl border border-primary/20 bg-primary/10 p-3 text-xs text-foreground-secondary">
              {saveMessage}
            </div>
          )}
          {plan ? (
            <div className="mt-5 space-y-4">
              <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4">
                <div className="flex gap-2">
                  <Bot className="mt-0.5 size-4 shrink-0 text-primary" />
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {plan.summary}
                    </p>
                    <p className="mt-2 text-xs leading-5 text-muted-foreground">
                      {plan.explanation}
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-xl bg-card p-3">
                  <p className="text-muted-foreground">Width</p>
                  <p className="mt-1 font-mono text-sm">{plan.spec.width_m}m</p>
                </div>
                <div className="rounded-xl bg-card p-3">
                  <p className="text-muted-foreground">Supports</p>
                  <p className="mt-1 font-mono text-sm">{plan.spec.supports}</p>
                </div>
                <div className="rounded-xl bg-card p-3">
                  <p className="text-muted-foreground">Deck level</p>
                  <p className="mt-1 font-mono text-sm">
                    {plan.spec.deck_elevation_m}m
                  </p>
                </div>
              </div>
              <div>
                <p className="mb-2 text-xs font-medium text-foreground-secondary">
                  Assumptions
                </p>
                {plan.assumptions.map((item) => (
                  <p
                    key={item}
                    className="mb-2 flex gap-2 text-xs leading-5 text-muted-foreground"
                  >
                    <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-primary" />
                    {item}
                  </p>
                ))}
              </div>
              {plan.warnings.map((item) => (
                <p key={item} className="text-xs leading-5 text-amber-200">
                  {item}
                </p>
              ))}
            </div>
          ) : (
            <div className="mt-5 rounded-2xl border border-dashed border-white/15 p-5 text-center">
              <WandSparkles className="mx-auto size-5 text-primary" />
              <p className="mt-2 text-sm text-foreground-secondary">
                Your site-aware concept will appear here.
              </p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                Nemotron creates a constrained BridgeSpec; the app procedurally
                renders it.
              </p>
            </div>
          )}
          <p className="mt-6 border-t border-border pt-4 text-[11px] leading-5 text-muted-foreground">
            Conceptual visualization only. Not a structural design, survey,
            safety assessment, cost estimate, permit application, or
            construction-ready plan.
          </p>
        </section>
      </main>
    </div>
  );
}

export default function GeoAIStudio(props: GeoAIStudioProps) {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-screen place-items-center bg-background text-sm text-muted-foreground">
          Loading workspace…
        </div>
      }
    >
      <GeoAIStudioContent {...props} />
    </Suspense>
  );
}
