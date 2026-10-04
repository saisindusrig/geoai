"use client";

import { AlertTriangle, MapPin, MousePointerClick, RefreshCw } from "lucide-react";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { CollapsibleSection } from "@/components/ui/collapsible-section";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { generateSiteSuggestions, type SiteSuggestion } from "@/lib/site-suggestions";
import type { GeoJSONFeature, ProjectType } from "@/lib/types";
import { useProjectStore } from "@/stores/projectStore";
import { toast } from "@/lib/toast";

interface Props {
  projectId?: number;
  projectType: ProjectType;
  centerLng: number;
  centerLat: number;
  roadFeatures?: GeoJSONFeature[];
  buildingFeatures?: GeoJSONFeature[];
  onApplyBoundary?: (s: SiteSuggestion) => void | Promise<void>;
  onApplyAlignment?: (s: SiteSuggestion) => void | Promise<void>;
  compact?: boolean;
  /** Slim sidebar: refresh + list only (no duplicate map-pick actions). */
  sidebar?: boolean;
  /** Load suggestions at project center when the panel mounts. */
  autoLoadOnMount?: boolean;
}

async function fetchSuggestions(
  projectId: number | undefined,
  lng: number,
  lat: number,
  projectType: ProjectType,
  roadFeatures: GeoJSONFeature[],
): Promise<SiteSuggestion[]> {
  if (projectId) {
    try {
      const res = await api.post<{ suggestions: SiteSuggestion[] }>(
        `/api/projects/${projectId}/site-suggestions`,
        { lng, lat },
      );
      return res.suggestions;
    } catch {
      /* fallback */
    }
  }
  return generateSiteSuggestions(lng, lat, projectType, roadFeatures);
}

export default function SiteSuggestionsPanel({
  projectId,
  projectType,
  centerLng,
  centerLat,
  roadFeatures = [],
  buildingFeatures = [],
  onApplyBoundary,
  onApplyAlignment,
  compact,
  sidebar,
  autoLoadOnMount,
}: Props) {
  const {
    activeTool,
    setActiveTool,
    siteSuggestions,
    setSiteSuggestions,
    highlightedSuggestionId,
    setHighlightedSuggestionId,
  } = useProjectStore();

  const refreshAtCenter = async () => {
    const list = await fetchSuggestions(projectId, centerLng, centerLat, projectType, roadFeatures);
    setSiteSuggestions(list);
    setHighlightedSuggestionId(list[0]?.id ?? null);
    if (!autoLoadOnMount) {
      toast("Site suggestions updated", {
        description: `${list.length} options shown on map`,
        variant: "success",
      });
    }
  };

  useEffect(() => {
    if (!autoLoadOnMount) return;
    let cancelled = false;
    void (async () => {
      const list = await fetchSuggestions(projectId, centerLng, centerLat, projectType, roadFeatures);
      if (cancelled) return;
      setSiteSuggestions(list);
      setHighlightedSuggestionId(list[0]?.id ?? null);
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoadOnMount, centerLng, centerLat, projectType, projectId]);

  const apply = async (s: SiteSuggestion) => {
    if (s.building_clashes?.length) {
      toast("Building overlap detected", {
        description: s.building_clashes[0],
        variant: "error",
      });
    }
    if (s.kind === "boundary") await onApplyBoundary?.(s);
    else await onApplyAlignment?.(s);
    toast(`Applied: ${s.label}`, { variant: "success" });
  };

  const displayList = siteSuggestions;

  const suggestionList = (
    <div className={cn("space-y-1 pr-0.5", sidebar ? "min-h-0 flex-1 overflow-y-auto overscroll-contain" : "max-h-[240px] overflow-y-auto")}>
      {displayList.length === 0 ? (
        <p className="text-[10px] text-muted-foreground px-1 py-2 leading-snug">
          {sidebar
            ? "No suggestions yet — use Suggest tool and click the map, or tap Refresh."
            : "Use Smart Suggest in Drawing Tools, then click the map."}
        </p>
      ) : (
        displayList.map((s) => (
          <button
            key={s.id}
            type="button"
            onMouseEnter={() => setHighlightedSuggestionId(s.id)}
            onMouseLeave={() => setHighlightedSuggestionId(null)}
            onClick={() => apply(s)}
            className={cn(
              "w-full text-left rounded-md border px-2 py-1.5 transition-colors duration-200",
              highlightedSuggestionId === s.id
                ? "border-accent/40 bg-accent/10"
                : s.building_clashes?.length
                  ? "border-warning/40 bg-warning/5"
                  : "border-border hover:border-primary/30 hover:bg-primary/5",
            )}
          >
            <div className="flex items-center justify-between gap-2 mb-0.5">
              <span className="text-[11px] font-medium truncate">{s.label}</span>
              <span className="text-[10px] font-data text-accent shrink-0">{s.score}%</span>
            </div>
            <p className="text-[10px] text-muted-foreground leading-snug line-clamp-2">{s.reason}</p>
            {s.building_clashes && s.building_clashes.length > 0 && (
              <p className="text-[9px] text-warning flex items-center gap-1 mt-1">
                <AlertTriangle className="h-3 w-3 shrink-0" />
                {s.building_clashes[0]}
              </p>
            )}
          </button>
        ))
      )}
    </div>
  );

  if (sidebar) {
    return (
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="mb-2 flex shrink-0 items-center justify-between gap-2 px-0.5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Site Suggestions
          </span>
          <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[10px] gap-1" onClick={refreshAtCenter}>
            <RefreshCw className="h-3 w-3" />
            Refresh
          </Button>
        </div>
        {buildingFeatures.length > 0 && (
          <p className="mb-1 shrink-0 text-[9px] text-muted-foreground px-0.5">
            {buildingFeatures.length} building(s) — clashes highlighted
          </p>
        )}
        {suggestionList}
      </div>
    );
  }

  const content = (
    <>
      {!compact && (
        <>
          <Button
            variant={activeTool === "suggest-site" ? "default" : "secondary"}
            size="sm"
            className="w-full justify-start gap-2 h-8 text-[11px]"
            onClick={() => {
              setActiveTool("suggest-site");
              toast("Click the map", { description: "Pick a point to generate suggestions there" });
            }}
          >
            <MousePointerClick className="h-3.5 w-3.5 shrink-0" />
            Pick location on map
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 h-7 text-[10px] text-muted-foreground"
            onClick={refreshAtCenter}
          >
            <MapPin className="h-3 w-3" />
            Suggest at project center
          </Button>
        </>
      )}

      {buildingFeatures.length > 0 && (
        <p className="text-[9px] text-muted-foreground px-1">
          {buildingFeatures.length} building(s) from analysis — clashes highlighted
        </p>
      )}

      {suggestionList}
    </>
  );

  if (compact) {
    return <div className="space-y-2">{content}</div>;
  }

  return (
    <div className="space-y-1">
      <CollapsibleSection title="Site Suggestions" defaultOpen>
        <div className="flex justify-end -mt-1 mb-1">
          <Button variant="ghost" size="sm" className="h-6 px-1.5 text-[10px] gap-1" onClick={refreshAtCenter}>
            <RefreshCw className="h-3 w-3" />
            Refresh
          </Button>
        </div>
        {content}
      </CollapsibleSection>
    </div>
  );
}
