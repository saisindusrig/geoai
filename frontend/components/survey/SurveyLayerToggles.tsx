"use client";

import { useProjectStore } from "@/stores/projectStore";
import { cn } from "@/lib/utils";

const TOGGLES: {
  key: keyof ReturnType<typeof useProjectStore.getState>["surveyLayers"];
  label: string;
  short: string;
  hint?: string;
}[] = [
  { key: "visualBasemap", label: "Visual satellite", short: "Satellite", hint: "Reference only — not for quantity takeoff" },
  { key: "surveyOrtho", label: "Survey ortho", short: "Ortho" },
  { key: "surveyDem", label: "DEM terrain mesh", short: "DEM" },
  { key: "surveyVectors", label: "Engineering vectors", short: "Vectors" },
  { key: "surveyGcp", label: "GCP points", short: "GCPs" },
];

export default function SurveyLayerToggles({ compact }: { compact?: boolean }) {
  const surveyLayers = useProjectStore((s) => s.surveyLayers);
  const toggleSurveyLayer = useProjectStore((s) => s.toggleSurveyLayer);

  if (compact) {
    return (
      <div className="grid grid-cols-3 gap-1">
        {TOGGLES.map(({ key, short, hint, label }) => {
          const pressed = surveyLayers[key];
          const title = hint ?? label;
          return (
            <button
              key={key}
              type="button"
              title={title}
              aria-label={label}
              {...(pressed ? { "aria-pressed": "true" as const } : { "aria-pressed": "false" as const })}
              onClick={() => toggleSurveyLayer(key)}
              className={cn(
                "rounded border px-1.5 py-1 text-[10px] font-medium transition-colors truncate",
                pressed
                  ? "border-primary/40 bg-primary/15 text-primary"
                  : "border-border bg-muted/40 text-muted-foreground hover:text-foreground",
              )}
            >
              {short}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Layer visibility</p>
      {TOGGLES.map(({ key, label, hint }) => (
        <label key={key} className="flex items-start gap-2 text-xs cursor-pointer">
          <input
            type="checkbox"
            checked={surveyLayers[key]}
            onChange={() => toggleSurveyLayer(key)}
            className="mt-0.5"
          />
          <span>
            {label}
            {hint && <span className="block text-[10px] text-muted-foreground">{hint}</span>}
          </span>
        </label>
      ))}
    </div>
  );
}
