"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, RotateCcw, Save, SlidersHorizontal } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { ProjectType, ProjectTemplate } from "@/lib/types";
import { projectTypeFamily, type ProjectTypeFamily } from "@/lib/project-catalog";
import { selectClassName } from "@/components/ui/select";
import { cn } from "@/lib/utils";

interface FieldDef {
  name: string;
  label: string;
  shortLabel?: string;
  unit?: string;
  step?: number;
  options?: string[];
}

const num = (min: number, max: number) => z.coerce.number().min(min).max(max);

const SCHEMAS: Record<ProjectTypeFamily, z.ZodObject<z.ZodRawShape>> = {
  flyover: z.object({
    length_m: num(50, 10000),
    deck_width_m: num(6, 60),
    lanes: num(1, 12),
    clearance_m: num(4, 12),
    pier_spacing_m: num(15, 60),
    foundation_depth_m_assumed: num(3, 40),
    concrete_grade: z.string(),
    asphalt_thickness_mm: num(40, 150),
  }),
  building: z.object({
    builtup_area_sqm: num(50, 100000),
    floors: num(1, 60),
    floor_height_m: num(2.5, 6),
    slab_thickness_m: num(0.1, 0.4),
    column_grid_m: num(3, 12),
    concrete_grade: z.string(),
  }),
  pipeline: z.object({
    length_m: num(10, 50000),
    pipe_diameter_mm: num(100, 3000),
    trench_width_m: num(0.6, 5),
    trench_depth_m: num(0.8, 10),
    utility_type: z.string(),
  }),
  road: z.object({
    length_m: num(50, 100000),
    road_width_m: num(3, 40),
    lanes: num(1, 10),
    asphalt_thickness_mm: num(40, 150),
    base_thickness_mm: num(100, 500),
    shoulder_width_m: num(0, 5),
  }),
};

const FIELDS: Record<ProjectTypeFamily, FieldDef[]> = {
  flyover: [
    { name: "length_m", label: "Length", unit: "m" },
    { name: "deck_width_m", label: "Deck width", shortLabel: "Deck w", unit: "m" },
    { name: "lanes", label: "Lanes" },
    { name: "clearance_m", label: "Vertical clearance", shortLabel: "Clearance", unit: "m", step: 0.1 },
    { name: "pier_spacing_m", label: "Pier spacing", shortLabel: "Pier space", unit: "m" },
    {
      name: "foundation_depth_m_assumed",
      label: "Foundation depth (assumed)",
      shortLabel: "Fdn depth",
      unit: "m",
    },
    { name: "concrete_grade", label: "Concrete grade", shortLabel: "Concrete" },
    { name: "asphalt_thickness_mm", label: "Asphalt thickness", shortLabel: "Asphalt", unit: "mm" },
  ],
  building: [
    { name: "builtup_area_sqm", label: "Built-up area / floor", shortLabel: "Area/floor", unit: "m²" },
    { name: "floors", label: "Floors" },
    { name: "floor_height_m", label: "Floor height", shortLabel: "Flr height", unit: "m", step: 0.1 },
    { name: "slab_thickness_m", label: "Slab thickness", shortLabel: "Slab", unit: "m", step: 0.01 },
    { name: "column_grid_m", label: "Column grid", shortLabel: "Col grid", unit: "m", step: 0.5 },
    { name: "concrete_grade", label: "Concrete grade", shortLabel: "Concrete" },
  ],
  pipeline: [
    { name: "length_m", label: "Alignment length", shortLabel: "Length", unit: "m" },
    { name: "pipe_diameter_mm", label: "Pipe diameter", shortLabel: "Pipe Ø", unit: "mm" },
    { name: "trench_width_m", label: "Trench width", shortLabel: "Trench w", unit: "m", step: 0.1 },
    { name: "trench_depth_m", label: "Trench depth", shortLabel: "Trench d", unit: "m", step: 0.1 },
    { name: "utility_type", label: "Utility type", shortLabel: "Utility" },
  ],
  road: [
    { name: "length_m", label: "Length", unit: "m" },
    { name: "road_width_m", label: "Carriageway width", shortLabel: "Width", unit: "m", step: 0.5 },
    { name: "lanes", label: "Lanes" },
    { name: "asphalt_thickness_mm", label: "Asphalt thickness", shortLabel: "Asphalt", unit: "mm" },
    { name: "base_thickness_mm", label: "Base thickness", shortLabel: "Base", unit: "mm" },
    { name: "shoulder_width_m", label: "Shoulder width", shortLabel: "Shoulder", unit: "m", step: 0.5 },
  ],
};

export const DEFAULTS: Record<ProjectTypeFamily, Record<string, number | string>> = {
  flyover: {
    length_m: 500, deck_width_m: 16, lanes: 4, clearance_m: 5.5, pier_spacing_m: 30,
    foundation_depth_m_assumed: 8, concrete_grade: "M35", asphalt_thickness_mm: 80,
  },
  building: {
    builtup_area_sqm: 400, floors: 4, floor_height_m: 3.2, slab_thickness_m: 0.15,
    column_grid_m: 5, concrete_grade: "M25",
  },
  pipeline: {
    length_m: 300, pipe_diameter_mm: 600, trench_width_m: 1.2, trench_depth_m: 2,
    utility_type: "drainage",
  },
  road: {
    length_m: 1000, road_width_m: 7.5, lanes: 2, asphalt_thickness_mm: 80,
    base_thickness_mm: 250, shoulder_width_m: 1.5,
  },
};

interface ParameterFormProps {
  projectType: ProjectType;
  initialValues?: Record<string, unknown> | null;
  onGenerate: (params: Record<string, unknown>) => void;
  generating: boolean;
  /** Narrow sidebar: 2-column grid + pinned generate button. */
  compact?: boolean;
  /** Horizontal strip for workspace top toolbar. */
  toolbar?: boolean;
}

const fieldInputClass = cn(
  "h-7 px-2 text-[11px] bg-background",
);
const fieldSelectClass = cn(
  selectClassName,
  "mt-0.5 h-7 px-2 py-1 text-[11px]",
);

import { assetSupportsGeneration } from "@/lib/asset-types";

export default function ParameterForm(props: ParameterFormProps) {
  if (!assetSupportsGeneration(props.projectType)) {
    return <p className="text-xs text-muted-foreground">This is a site reference asset. Engineering generation and asset-specific quantities are unavailable.</p>;
  }
  return <SupportedParameterForm {...props} />;
}

function SupportedParameterForm({
  projectType,
  initialValues,
  onGenerate,
  generating,
  compact,
  toolbar,
}: ParameterFormProps) {
  const family = projectTypeFamily(projectType);
  const fields = FIELDS[family];
  const [paramsOpen, setParamsOpen] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [panelPos, setPanelPos] = useState<{ top: number; right: number } | null>(null);
  const paramsBtnRef = useRef<HTMLButtonElement>(null);
  const [designInstructions, setDesignInstructions] = useState("");
  const form = useForm({
    resolver: zodResolver(SCHEMAS[family]),
    defaultValues: { ...DEFAULTS[family], ...(initialValues ?? {}) },
  });

  useEffect(() => {
    if (initialValues) return;
    let cancelled = false;
    api
      .get<ProjectTemplate[]>(`/api/templates?project_type=${encodeURIComponent(projectType)}`)
      .then((templates) => {
        if (cancelled) return;
        const match =
          templates.find((t) => t.project_type === projectType) ??
          templates.find((t) => projectTypeFamily(t.project_type as ProjectType) === family);
        if (!match?.default_parameters_json) return;
        const merged = { ...DEFAULTS[family], ...match.default_parameters_json, ...(initialValues ?? {}) };
        form.reset(merged);
      })
      .catch(() => {
        /* keep local defaults */
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectType, family]);

  useEffect(() => {
    if (initialValues) {
      form.reset({ ...DEFAULTS[family], ...initialValues });
      const instr = initialValues.design_instructions ?? initialValues.custom_instructions;
      if (typeof instr === "string") setDesignInstructions(instr);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialValues, family]);

  const submitParams = (values: Record<string, unknown>) => {
    const trimmed = designInstructions.trim();
    onGenerate({
      ...values,
      ...(trimmed ? { design_instructions: trimmed } : {}),
    });
  };

  const updatePanelPos = useCallback(() => {
    const btn = paramsBtnRef.current;
    if (!btn) return;
    const rect = btn.getBoundingClientRect();
    setPanelPos({
      top: Math.min(rect.bottom + 8, window.innerHeight - 520),
      right: Math.max(12, window.innerWidth - rect.right),
    });
  }, []);

  useEffect(() => {
    if (!toolbar || !paramsOpen) return;
    updatePanelPos();
    window.addEventListener("resize", updatePanelPos);
    window.addEventListener("scroll", updatePanelPos, true);
    return () => {
      window.removeEventListener("resize", updatePanelPos);
      window.removeEventListener("scroll", updatePanelPos, true);
    };
  }, [toolbar, paramsOpen, updatePanelPos]);

  useEffect(() => {
    if (!paramsOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setParamsOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [paramsOpen]);

  const renderField = (f: FieldDef) => {
    const error = form.formState.errors[f.name];
    const displayLabel = toolbar
      ? (f.shortLabel ?? f.label)
      : compact
        ? (f.shortLabel ?? f.label)
        : f.label;

    if (toolbar) {
      return (
        <label key={f.name} className="shrink-0 flex flex-col min-w-0" title={f.label}>
          <span className="text-[9px] font-medium text-muted-foreground truncate max-w-[72px]">
            {displayLabel}
            {f.unit && <span className="text-muted-foreground/70"> ({f.unit})</span>}
          </span>
          {f.options ? (
            <select {...form.register(f.name)} className={cn(fieldSelectClass, "w-[72px]")}>
              {f.options.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          ) : (
            <Input
              type="number"
              step={f.step ?? 1}
              {...form.register(f.name)}
              className={cn(fieldInputClass, "mt-0.5 w-[72px]")}
            />
          )}
          {error && (
            <span className="text-[9px] text-destructive leading-tight max-w-[72px] truncate">
              {String(error.message)}
            </span>
          )}
        </label>
      );
    }

    return (
      <label key={f.name} className="block min-w-0" title={f.label}>
        <span
          className={cn(
            "block truncate font-medium text-muted-foreground",
            compact ? "text-[10px] leading-tight" : "text-xs text-muted-foreground",
          )}
        >
          {displayLabel}
          {f.unit && !compact && <span className="text-muted-foreground/70"> ({f.unit})</span>}
          {f.unit && compact && <span className="text-muted-foreground/70"> ({f.unit})</span>}
        </span>
        {f.options ? (
          <select {...form.register(f.name)} className={fieldSelectClass}>
            {f.options.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        ) : (
          <Input
            type="number"
            step={f.step ?? 1}
            {...form.register(f.name)}
            className={cn(fieldInputClass, compact ? "mt-0.5" : "mt-0.5")}
          />
        )}
        {error && (
          <span className="text-[10px] text-destructive leading-tight">{String(error.message)}</span>
        )}
      </label>
    );
  };

  if (toolbar) {
    // React Hook Form watch() is intentionally used for live toolbar summary text.
    // eslint-disable-next-line react-hooks/incompatible-library -- RHF watch for toolbar preview
    const watched = form.watch();
    const summaryParts: string[] = [];
    if (family === "flyover") {
      if (watched.length_m != null) summaryParts.push(`${watched.length_m}m`);
      if (watched.lanes != null) summaryParts.push(`${watched.lanes} ln`);
    } else if (family === "building") {
      if (watched.floors != null) summaryParts.push(`${watched.floors} fl`);
    } else if (family === "road" || family === "pipeline") {
      if (watched.length_m != null) summaryParts.push(`${watched.length_m}m`);
    }
    const isMobile = typeof window !== "undefined" && window.innerWidth < 768;

    return (
      <form
        id="parameters-panel"
        onSubmit={form.handleSubmit((values) => {
          setParamsOpen(false);
          submitParams(values);
        })}
        className="relative flex items-center gap-1.5 shrink-0"
      >
        <Button
          ref={paramsBtnRef}
          type="button"
          variant="secondary"
          size="sm"
          className={cn(
            "h-8 gap-1.5 rounded-lg border-border bg-background-secondary/90 px-2 text-[11px] text-foreground-secondary hover:border-[rgba(34,211,238,0.35)] hover:bg-[rgba(34,211,238,0.1)] hover:text-foreground",
            paramsOpen && "border-[rgba(34,211,238,0.38)] bg-[rgba(34,211,238,0.12)] text-[#A5F3FC]",
          )}
          onClick={() => {
            setParamsOpen((v) => {
              const next = !v;
              if (next) requestAnimationFrame(updatePanelPos);
              return next;
            });
          }}
          aria-expanded={paramsOpen}
          aria-haspopup="dialog"
        >
          <SlidersHorizontal className="h-3.5 w-3.5 shrink-0" />
          <span className="hidden sm:inline">Params</span>
          {summaryParts.length > 0 && (
            <span className="hidden md:inline text-muted-foreground font-data text-[10px]">
              · {summaryParts.join(" · ")}
            </span>
          )}
        </Button>

        {paramsOpen &&
          panelPos &&
          typeof document !== "undefined" &&
          createPortal(
            <>
              <button
                type="button"
                aria-label="Close parameters"
                className="fixed inset-0 z-[100] cursor-default bg-transparent"
                onClick={() => setParamsOpen(false)}
              />
              <div
                role="dialog"
                aria-label="Design parameters"
                className="fixed inset-x-3 bottom-3 z-[101] max-h-[calc(100vh-5rem)] overflow-hidden rounded-2xl border border-border bg-[rgba(11,17,28,0.98)] shadow-2xl backdrop-blur-xl md:inset-x-auto md:bottom-auto md:w-[min(100vw-2rem,440px)]"
                style={isMobile ? undefined : { top: panelPos.top, right: panelPos.right }}
              >
                <div className="flex max-h-[inherit] flex-col overflow-hidden">
                  <div className="shrink-0 border-b border-[rgba(148,163,184,0.14)] px-4 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                          Design Parameters
                        </p>
                        <p className="mt-1 text-[12px] leading-snug text-muted-foreground">
                          Preliminary AI concept values for the active infrastructure scenario.
                        </p>
                      </div>
                      <span className="rounded-full border border-[var(--primary)] bg-[rgba(59,130,246,0.12)] px-2 py-1 text-[10px] text-foreground-secondary">
                        {family}
                      </span>
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto p-4 scrollbar-thin-dark">
                    <div className="grid grid-cols-2 gap-2">
                      {fields.map((f) => {
                        const error = form.formState.errors[f.name];
                        const displayLabel = f.shortLabel ?? f.label;
                        return (
                          <label key={f.name} className="block min-w-0" title={f.label}>
                            <span className="mb-1 flex items-center justify-between gap-2 text-[10px] font-medium text-muted-foreground">
                              <span className="truncate">{displayLabel}</span>
                              {f.unit && (
                                <span className="shrink-0 rounded bg-white/[0.05] px-1.5 py-0.5 font-data text-[9px] text-muted-foreground">
                                  {f.unit}
                                </span>
                              )}
                            </span>
                            {f.options ? (
                              <select
                                {...form.register(f.name)}
                                className={cn(
                                  fieldSelectClass,
                                  "w-full border-border bg-background font-data text-foreground",
                                  error && "border-[#EF4444] shadow-[0_0_0_2px_rgba(239,68,68,0.16)]",
                                )}
                              >
                                {f.options.map((o) => (
                                  <option key={o} value={o}>
                                    {o}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <Input
                                type={f.name.includes("grade") || f.name.includes("type") ? "text" : "number"}
                                step={f.step ?? 1}
                                {...form.register(f.name)}
                                className={cn(
                                  fieldInputClass,
                                  "mt-0.5 w-full border-border bg-background font-data text-foreground",
                                  error && "border-[#EF4444] shadow-[0_0_0_2px_rgba(239,68,68,0.16)]",
                                )}
                              />
                            )}
                            {error && (
                              <span className="mt-1 block text-[9px] leading-tight text-[#F87171]">
                                {String(error.message)}
                              </span>
                            )}
                          </label>
                        );
                      })}
                    </div>

                    <button
                      type="button"
                      onClick={() => setAdvancedOpen((v) => !v)}
                      className="mt-4 flex w-full items-center justify-between rounded-lg border border-[rgba(148,163,184,0.14)] bg-white/[0.03] px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                    >
                      Advanced assumptions
                      <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", advancedOpen && "rotate-180")} />
                    </button>
                    {advancedOpen && (
                      <div className="mt-2 grid grid-cols-2 gap-2">
                        {[
                          ["Design speed", "60 km/h"],
                          ["Barrier type", "Crash barrier"],
                          ["Pier type", "Single shaft"],
                          ["Foundation type", "Pile cap"],
                          ["Seismic zone", "II/III"],
                          ["Soil bearing", "Verify survey"],
                        ].map(([label, value]) => (
                          <div
                            key={label}
                            className="rounded-lg border border-border bg-background px-2.5 py-2"
                          >
                            <p className="text-[9px] uppercase tracking-wide text-muted-foreground">{label}</p>
                            <p className="mt-1 truncate font-data text-[11px] text-foreground-secondary">{value}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    <p className="mt-3 rounded-lg border border-[rgba(245,158,11,0.22)] bg-[rgba(245,158,11,0.08)] px-3 py-2 text-[10px] leading-snug text-[#FCD34D]">
                      Preliminary AI concept only. Verify with licensed engineers and survey data before construction.
                    </p>

                    <label className="mt-3 block">
                      <span className="mb-1 block text-[10px] font-medium text-muted-foreground">
                        Design instructions
                      </span>
                      <textarea
                        value={designInstructions}
                        onChange={(e) => setDesignInstructions(e.target.value)}
                        rows={3}
                        placeholder="e.g. 4-lane flyover, 5.5m clearance, economical pier spacing, add drainage"
                        className="w-full resize-none rounded-lg border border-border bg-background px-2.5 py-2 text-[11px] text-foreground placeholder:text-muted-foreground focus:border-[var(--primary)] focus:outline-none"
                      />
                      <span className="mt-1 block text-[9px] text-muted-foreground">
                        Optional — sent to AI planner for parameter suggestions (not 3D mesh).
                      </span>
                    </label>
                  </div>

                  <div className="grid shrink-0 grid-cols-3 gap-2 border-t border-[rgba(148,163,184,0.14)] p-3">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      className="h-8 gap-1 text-[11px]"
                      onClick={() => form.reset(DEFAULTS[family])}
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                      Reset
                    </Button>
                    <Button
                      type="submit"
                      disabled={generating}
                      size="sm"
                      className="h-8 gap-1 btn-primary-gradient text-[11px]"
                    >
                      Apply
                    </Button>
                    <Button
                      type="submit"
                      disabled={generating}
                      variant="secondary"
                      size="sm"
                      className="h-8 gap-1 text-[11px]"
                      title="Creates a generated scenario with these parameters"
                    >
                      <Save className="h-3.5 w-3.5" />
                      Scenario
                    </Button>
                  </div>
                </div>
              </div>
            </>,
            document.body,
          )}

        <Button type="submit" disabled={generating} size="sm" className={cn(
          "h-8 shrink-0 text-[11px] px-3 gap-1.5  hover:brightness-110 shadow-[var(--shadow-glow-primary)]",
          generating && "opacity-80",
        )}>
          {generating ? "Generating…" : "Generate"}
        </Button>
      </form>
    );
  }

  return (
    <form
      onSubmit={form.handleSubmit((values) => submitParams(values))}
      className={cn(compact ? "flex flex-col gap-2" : "space-y-3")}
    >
      <div
        className={cn(
          compact
            ? "grid grid-cols-2 gap-x-2 gap-y-2 content-start"
            : "space-y-3",
        )}
      >
        {fields.map(renderField)}
      </div>
      <label className="block">
        <span className="mb-1 block text-[10px] font-medium text-muted-foreground">
          Design instructions
        </span>
        <textarea
          value={designInstructions}
          onChange={(e) => setDesignInstructions(e.target.value)}
          rows={2}
          placeholder="Optional AI planning instructions…"
          className="w-full resize-none rounded-md border border-input bg-background px-2 py-1.5 text-[11px] focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </label>
      <Button
        type="submit"
        disabled={generating}
        size="sm"
        className={cn(
          "w-full shrink-0",
          compact ? "h-8 text-[11px]" : "mt-auto h-9",
        )}
      >
        {generating ? "Generating…" : compact ? "Generate Design" : "Generate Preliminary Design"}
      </Button>
    </form>
  );
}
