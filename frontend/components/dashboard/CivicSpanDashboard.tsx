"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Clock3,
  MapPinned,
  Plus,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import { CONSTRUCTION_LABELS, CONSTRUCTION_TYPES } from "@/lib/construction";
import type { Project } from "@/lib/types";
import CreativeDashboard from "@/components/dashboard/CreativeDashboard";

const STARTERS = [
  [
    "Pedestrian bridge",
    "A safe, accessible walking connection across a local crossing.",
    "bridge",
    "Bridge",
  ],
  [
    "Flyover / overpass",
    "An elevated road connection with piers, deck, and edge barriers.",
    "flyover",
    "Transport",
  ],
  [
    "Building massing",
    "A site-aware public building volume with a practical structural grid.",
    "building",
    "Structure",
  ],
  [
    "Road corridor",
    "A two-lane road concept with shoulders and a clear site alignment.",
    "road",
    "Infrastructure",
  ],
  [
    "Pipeline corridor",
    "A maintainable utility route with access chambers and safe spacing.",
    "pipeline",
    "Utilities",
  ],
  [
    "Dam / reservoir",
    "A conceptual gravity dam with foundation, spillway, and reservoir wall.",
    "dam",
    "Water works",
  ],
] as const;

function location(project: Project) {
  if (project.location_name) return project.location_name;
  return project.center_lat != null && project.center_lng != null
    ? `${project.center_lat.toFixed(4)}, ${project.center_lng.toFixed(4)}`
    : "Map location not saved";
}

function updated(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Recently updated";
  return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(
    Math.round((date.getTime() - Date.now()) / 86_400_000),
    "day",
  );
}

const tileTone = [
  "bg-[linear-gradient(135deg,rgba(178,187,171,0.26),rgba(75,92,88,0.18))]",
  "bg-[linear-gradient(135deg,rgba(142,160,163,0.24),rgba(75,92,88,0.18))]",
  "bg-[linear-gradient(135deg,rgba(178,187,171,0.18),rgba(142,160,163,0.16))]",
];

export function LegacyGeoAIDashboard() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(
    () =>
      api
        .get<Project[]>("/api/projects")
        .then((list) => {
          setProjects(list);
          setError(null);
        })
        .catch(() => {
          setProjects([]);
          setError(
            "Saved concepts are unavailable while the local backend is offline.",
          );
        }),
    [],
  );

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(() => {
    const search = query.trim().toLowerCase();
    const concepts = (projects ?? []).filter((project) =>
      CONSTRUCTION_TYPES.includes(
        project.project_type as (typeof CONSTRUCTION_TYPES)[number],
      ),
    );
    return search
      ? concepts.filter((project) =>
          `${project.name} ${location(project)}`.toLowerCase().includes(search),
        )
      : concepts;
  }, [projects, query]);

  const remove = async (project: Project) => {
    if (!confirm(`Delete “${project.name}”? This cannot be undone.`)) return;
    await api.delete(`/api/projects/${project.id}`);
    load();
  };

  return (
    <div className="min-w-[1280px] flex-1 overflow-y-auto bg-background">
      <div className="mx-auto max-w-[1480px] px-10 py-9">
        <header className="flex items-center justify-between gap-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
              GeoAI home
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground">
              What will you create?
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Start a site-aware construction concept or return to a saved
              workspace.
            </p>
          </div>
          <Link href="/projects/new" className="shrink-0">
            <span className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-sm)] transition hover:bg-primary-hover">
              <Plus className="size-4" />
              Create a concept
            </span>
          </Link>
        </header>
        <section className="mt-9 rounded-[1.5rem] border border-border bg-[radial-gradient(ellipse_at_top_left,rgba(178,187,171,0.2),transparent_42%),var(--card)] p-8 shadow-[var(--shadow-md)]">
          <div className="flex items-end justify-between gap-8">
            <div className="max-w-2xl">
              <div className="mb-5 inline-flex size-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
                <Sparkles className="size-5" />
              </div>
              <h2 className="text-2xl font-semibold tracking-tight">
                From map click to 3D construction concept
              </h2>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                Choose endpoints, ask Nemotron to shape the concept, inspect
                every construction stage, and save only when you are ready.
              </p>
            </div>
            <Link
              href="/projects/new"
              className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-primary/40 bg-primary/10 px-4 py-3 text-sm font-semibold text-foreground-secondary transition hover:bg-primary/20"
            >
              Open workspace <ArrowRight className="size-4" />
            </Link>
          </div>
        </section>
        <section className="mt-10">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Start creating</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Begin with any construction template, then make it your own.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-5">
            {STARTERS.map(([name, description, template, badge], index) => (
              <Link
                key={name}
                href={`/projects/new?template=${template}`}
                className="group rounded-2xl border border-border bg-card p-5 shadow-[var(--shadow-sm)] transition duration-200 hover:-translate-y-0.5 hover:border-primary/45 hover:shadow-[var(--shadow-md)]"
              >
                <div
                  className={`flex h-32 items-end rounded-xl border border-border/70 p-4 ${tileTone[index]}`}
                >
                  <span className="rounded-full border border-border bg-background/80 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-foreground-secondary">
                    {badge}
                  </span>
                </div>
                <h3 className="mt-4 font-semibold text-foreground">{name}</h3>
                <p className="mt-1 text-sm leading-5 text-muted-foreground">
                  {description}
                </p>
                <p className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-primary">
                  Use template{" "}
                  <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
                </p>
              </Link>
            ))}
          </div>
        </section>
        <section className="mt-11">
          <div className="flex items-end justify-between gap-5">
            <div>
              <h2 className="text-lg font-semibold">Recent concepts</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Continue refining saved construction workspaces.
              </p>
            </div>
            <label className="relative block w-72">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search concepts"
                className="h-10 w-full rounded-xl border border-border bg-card pl-9 pr-3 text-sm text-foreground outline-none focus:border-primary"
              />
            </label>
          </div>
          {error && (
            <p className="mt-4 rounded-xl border border-warning/25 bg-warning/10 px-4 py-3 text-sm text-warning-text">
              {error}
            </p>
          )}
          {projects === null && (
            <div className="mt-5 grid grid-cols-3 gap-5">
              {[0, 1, 2].map((item) => (
                <div
                  key={item}
                  className="h-44 animate-pulse rounded-2xl border border-border bg-card"
                />
              ))}
            </div>
          )}
          {projects !== null && visible.length === 0 && !error && (
            <div className="mt-5 rounded-2xl border border-dashed border-border bg-card px-7 py-12 text-center">
              <MapPinned className="mx-auto size-6 text-primary" />
              <h3 className="mt-3 font-semibold">
                No saved construction concepts yet
              </h3>
              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
                Open a workspace, set a crossing, generate your first concept,
                and save it here when it is ready.
              </p>
              <Link
                href="/projects/new"
                className="mt-5 inline-flex rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground"
              >
                Create a concept
              </Link>
            </div>
          )}
          {visible.length > 0 && (
            <div className="mt-5 grid grid-cols-3 gap-5">
              {visible.map((project, index) => (
                <article
                  key={project.id}
                  className="group overflow-hidden rounded-2xl border border-border bg-card shadow-[var(--shadow-sm)] transition hover:border-primary/45 hover:shadow-[var(--shadow-md)]"
                >
                  <Link
                    href={`/projects/${project.id}/workspace`}
                    className="block"
                  >
                    <div
                      className={`flex h-28 items-end justify-between border-b border-border p-4 ${tileTone[index % tileTone.length]}`}
                    >
                      <span className="rounded-full border border-border bg-background/80 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-foreground-secondary">
                        {CONSTRUCTION_LABELS[
                          project.project_type as keyof typeof CONSTRUCTION_LABELS
                        ] ?? "Construction concept"}
                      </span>
                      <ArrowRight className="size-4 text-primary transition-transform group-hover:translate-x-0.5" />
                    </div>
                    <div className="p-4">
                      <h3 className="truncate font-semibold text-foreground">
                        {project.name}
                      </h3>
                      <p className="mt-2 flex items-center gap-1.5 truncate text-xs text-muted-foreground">
                        <MapPinned className="size-3.5 shrink-0" />
                        {location(project)}
                      </p>
                      <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Clock3 className="size-3.5" />
                        {updated(project.updated_at)}
                      </p>
                    </div>
                  </Link>
                  <div className="flex border-t border-border px-4 py-3">
                    <Link
                      href={`/projects/${project.id}/workspace`}
                      className="text-xs font-semibold text-primary hover:text-primary-hover"
                    >
                      Open workspace
                    </Link>
                    <button
                      type="button"
                      onClick={() => remove(project)}
                      className="ml-auto text-muted-foreground transition hover:text-destructive"
                      aria-label={`Delete ${project.name}`}
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default CreativeDashboard;
