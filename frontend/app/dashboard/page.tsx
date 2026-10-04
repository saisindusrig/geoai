"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import GeoAIDashboard from "@/components/dashboard/CivicSpanDashboard";
import {
  ArrowRight,
  Check,
  Circle,
  FolderOpen,
  MapPin,
  Pencil,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import ApiErrorDetails from "@/components/ui/api-error-details";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { StatCard } from "@/components/ui/stat-card";
import WizardStepper from "@/components/ui/wizard-stepper";
import { computeHealth, type ProjectHealth } from "@/lib/project-workflow";
import { api, ApiError } from "@/lib/api";
import type { ParsedApiError } from "@/lib/api-errors";
import { loginPath } from "@/lib/auth-routes";
import { parseScenarioList } from "@/lib/scenario-api";
import { useAuthUser } from "@/lib/useAuthUser";
import type {
  DesignScenario,
  Project,
  ScenarioListResponse,
  ScenarioSummary,
  SiteAnalysis,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const TYPE_VARIANT: Record<
  string,
  "primary" | "accent" | "warning" | "success"
> = {
  flyover: "primary",
  bridge: "accent",
  building: "accent",
  pipeline: "warning",
  road: "success",
};

const HEALTH_LABELS: { key: keyof ProjectHealth; label: string }[] = [
  { key: "hasLocation", label: "Site" },
  { key: "hasBoundary", label: "Boundary" },
  { key: "hasAnalysis", label: "Analysis" },
  { key: "hasParameters", label: "Params" },
  { key: "hasDesign", label: "Design" },
  { key: "hasEstimate", label: "BOQ" },
];

const EMPTY_STEPS = ["Create project", "Draw site", "Generate design"] as const;

async function fetchProjectHealth(project: Project): Promise<ProjectHealth> {
  let scenarios: DesignScenario[] = [];
  let hasEstimate = false;
  let hasAnalysis = false;
  try {
    const scenarioRes = await api.get<ScenarioListResponse | ScenarioSummary[]>(
      `/api/projects/${project.id}/scenarios`,
    );
    scenarios = parseScenarioList(scenarioRes).map((s) => ({
      id: s.scenario_id,
      name: s.name,
      status: s.status,
      created_at: s.created_at ?? "",
      input_parameters_json: null,
      design_output_json:
        s.status === "completed"
          ? ({} as DesignScenario["design_output_json"])
          : null,
      assumptions_json: null,
    }));
  } catch {
    /* ignore */
  }
  try {
    const estimate = await api.getOptional(
      `/api/projects/${project.id}/estimates`,
    );
    hasEstimate = estimate != null;
  } catch {
    /* ignore */
  }
  try {
    const analysis = await api.getOptional<SiteAnalysis>(
      `/api/projects/${project.id}/site-analysis`,
    );
    hasAnalysis = analysis != null;
  } catch {
    /* ignore */
  }
  return computeHealth(project, scenarios, hasEstimate, hasAnalysis);
}

function HealthStrip({ health }: { health: ProjectHealth }) {
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {HEALTH_LABELS.map(({ key, label }) => {
        const done = health[key] as boolean;
        return (
          <span
            key={key}
            className={cn(
              "inline-flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded-md border",
              done
                ? "border-success/30 bg-success/10 text-success"
                : "border-border text-muted-foreground",
            )}
          >
            {done ? (
              <Check className="h-2.5 w-2.5" />
            ) : (
              <Circle className="h-2.5 w-2.5 opacity-40" />
            )}
            {label}
          </span>
        );
      })}
    </div>
  );
}

function ProgressRing({ value, size = 44 }: { value: number; size?: number }) {
  const r = (size - 6) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.min(100, Math.max(0, value));
  const offset = c - (clamped / 100) * c;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={3}
          className="stroke-muted/40"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={3}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="stroke-primary transition-all duration-500"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[10px] font-data font-semibold text-foreground">
        {clamped}%
      </span>
    </div>
  );
}

async function loadProjectsWithHealth() {
  const list = await api.get<Project[]>("/api/projects");
  let healthEntries: [number, ProjectHealth][] = [];
  try {
    const summaries = await api.get<
      {
        project_id: number;
        has_location: boolean;
        has_boundary: boolean;
        has_analysis: boolean;
        has_parameters: boolean;
        has_design: boolean;
        has_estimate: boolean;
        scenario_count: number;
        progress: number;
      }[]
    >("/api/projects/summaries");
    healthEntries = summaries.map((s) => [
      s.project_id,
      {
        hasLocation: s.has_location,
        hasBoundary: s.has_boundary,
        hasAnalysis: s.has_analysis,
        hasParameters: s.has_parameters,
        hasDesign: s.has_design,
        hasEstimate: s.has_estimate,
        scenarioCount: s.scenario_count,
        progress: s.progress,
      },
    ]);
  } catch {
    healthEntries = await Promise.all(
      list.map(async (p) => [p.id, await fetchProjectHealth(p)] as const),
    );
  }
  return {
    list,
    healthMap: Object.fromEntries(healthEntries) as Record<
      number,
      ProjectHealth
    >,
  };
}

export function LegacyDashboardPage() {
  const { isAdmin } = useAuthUser();
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [healthMap, setHealthMap] = useState<Record<number, ProjectHealth>>({});
  const [error, setError] = useState<ParsedApiError | null>(null);

  const load = () =>
    loadProjectsWithHealth()
      .then(({ list, healthMap: hm }) => {
        setProjects(list);
        setHealthMap(hm);
        setError(null);
      })
      .catch((e) => {
        if (e instanceof ApiError) setError(e.toParsed());
        else
          setError({
            status: 0,
            message: String(e instanceof Error ? e.message : e),
          });
      });

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    if (!projects) return null;
    const bridgeConcepts = projects.filter(
      (p) => p.project_type === "bridge",
    ).length;
    const readyToContinue = projects.filter(
      (p) => p.status !== "completed",
    ).length;
    return { total: projects.length, bridgeConcepts, readyToContinue };
  }, [projects]);

  const remove = async (id: number) => {
    if (!confirm("Delete this project and all its data?")) return;
    await api.delete(`/api/projects/${id}`);
    load();
  };

  const removeAll = async () => {
    if (!projects?.length) return;
    if (
      !confirm(
        `Delete all ${projects.length} projects and their data? This cannot be undone.`,
      )
    )
      return;
    await Promise.all(
      projects.map((project) => api.delete(`/api/projects/${project.id}`)),
    );
    load();
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        <PageHeader
          title="Bridge Concept Dashboard"
          description="Saved GeoAI site-aware bridge concepts"
          actions={
            <>
              <Link href="/projects/new">
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  New concept
                </Button>
              </Link>
              {isAdmin && projects && projects.length > 0 && (
                <Button
                  variant="destructive"
                  className="gap-2"
                  onClick={removeAll}
                >
                  <Trash2 className="h-4 w-4" />
                  Clear Projects
                </Button>
              )}
            </>
          }
        />

        {stats && (
          <div className="grid sm:grid-cols-3 gap-4">
            <StatCard
              label="Saved concepts"
              value={stats.total}
              icon={FolderOpen}
            />
            <StatCard
              label="Bridge concepts"
              value={stats.bridgeConcepts}
              sub="GeoAI workspaces"
              icon={Sparkles}
            />
            <StatCard
              label="Ready to continue"
              value={stats.readyToContinue}
              sub="Open and refine"
              icon={Pencil}
            />
          </div>
        )}

        {error && (
          <Card className="border-destructive/30 bg-destructive/5 p-4 space-y-3">
            <ApiErrorDetails error={error} />
            {error.status === 401 && (
              <Link href={loginPath("/dashboard")}>
                <Button size="sm" variant="secondary">
                  Sign in
                </Button>
              </Link>
            )}
            {error.status === 0 && (
              <p className="text-xs text-muted-foreground">
                Start the backend at localhost:8000 if you are developing
                locally.
              </p>
            )}
          </Card>
        )}

        <div className="grid sm:grid-cols-3 gap-4">
          <Link href="/projects/new">
            <Card
              float
              className="hover:border-primary/40 cursor-pointer h-full group"
            >
              <CardHeader>
                <div className="flex h-10 w-10 items-center justify-center bg-primary/10 group-hover:bg-primary/15 transition-colors">
                  <Plus className="h-5 w-5 text-accent" />
                </div>
                <CardTitle>New bridge concept</CardTitle>
                <CardDescription>
                  Open the workspace, place endpoints, and plan with Nemotron
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        </div>

        <div>
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <FolderOpen className="h-4 w-4 text-accent" />
            Saved concepts
          </h2>

          {!projects && !error && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          )}

          {projects && projects.length === 0 && (
            <Card className="border-dashed p-8 sm:p-12">
              <div className="max-w-lg mx-auto space-y-6 text-center">
                <MapPin className="h-10 w-10 text-muted-foreground mx-auto" />
                <div>
                  <p className="font-medium mb-1">No projects yet</p>
                  <p className="text-sm text-muted-foreground">
                    Open the workspace, select a crossing, and save when your
                    concept is ready.
                  </p>
                </div>
                <WizardStepper steps={EMPTY_STEPS} current={0} />
                <div className="grid gap-3 text-left text-xs text-muted-foreground sm:grid-cols-3">
                  <div className="rounded-lg border border-border/60 p-3">
                    <p className="font-semibold text-foreground mb-1">
                      1. Open
                    </p>
                    Start directly in the bridge workspace—no setup wizard.
                  </div>
                  <div className="rounded-lg border border-border/60 p-3">
                    <p className="font-semibold text-foreground mb-1">
                      2. Place
                    </p>
                    Select the bridge start and end points on the map.
                  </div>
                  <div className="rounded-lg border border-border/60 p-3">
                    <p className="font-semibold text-foreground mb-1">
                      3. Save
                    </p>
                    Generate a Nemotron concept, then save it to this dashboard.
                  </div>
                </div>
                <Link href="/projects/new">
                  <Button size="sm">Open workspace</Button>
                </Link>
              </div>
            </Card>
          )}

          <div className="grid gap-3">
            {projects?.map((p) => {
              const health = healthMap[p.id];
              return (
                <Card
                  key={p.id}
                  float
                  className="hover:border-primary/40 transition-colors"
                >
                  <CardContent className="p-4 flex items-start gap-4 flex-wrap">
                    {health && <ProgressRing value={health.progress} />}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <Link
                          href={`/projects/${p.id}/workspace`}
                          className="font-semibold hover:text-accent transition-colors truncate"
                        >
                          {p.name}
                        </Link>
                        <Badge
                          variant={TYPE_VARIANT[p.project_type] ?? "default"}
                        >
                          {p.project_type}
                        </Badge>
                        <Badge variant="default">{p.status}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground truncate flex items-center gap-1">
                        <MapPin className="h-3 w-3 shrink-0" />
                        {p.location_name ||
                          (p.center_lat != null
                            ? `${p.center_lat.toFixed(5)}, ${p.center_lng?.toFixed(5)}`
                            : "No location set")}
                      </p>
                      {health && <HealthStrip health={health} />}
                    </div>
                    <div className="flex gap-2 shrink-0 flex-wrap">
                      <Link href={`/projects/${p.id}/workspace`}>
                        <Button size="sm" variant="secondary" className="gap-1">
                          Open workspace <ArrowRight className="h-3 w-3" />
                        </Button>
                      </Link>
                      {p.project_type !== "bridge" && (
                        <Link href={`/projects/${p.id}/estimate`}>
                          <Button size="sm" variant="outline">
                            BOQ
                          </Button>
                        </Link>
                      )}
                      {p.project_type !== "bridge" &&
                        health &&
                        health.scenarioCount > 1 && (
                          <Link href={`/projects/${p.id}/scenarios`}>
                            <Button size="sm" variant="outline">
                              Compare
                            </Button>
                          </Link>
                        )}
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => remove(p.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        <DisclaimerBanner />
      </div>
    </div>
  );
}

export default GeoAIDashboard;
