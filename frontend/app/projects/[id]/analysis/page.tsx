"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Building2, MapPin, Mountain, Route, ScanSearch, TriangleAlert } from "lucide-react";
import { ProjectError, ProjectLoading } from "@/components/layout/ProjectHeader";
import MetricCard from "@/components/project-results/MetricCard";
import ProjectResultShell from "@/components/project-results/ProjectResultShell";
import ResultPageHeader from "@/components/project-results/ResultPageHeader";
import RiskList from "@/components/project-results/RiskList";
import EmptyState from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { useProjectData } from "@/hooks/useProjectData";
import { api } from "@/lib/api";
import { formatArea, formatDistance } from "@/lib/geo";
import type { GeoJSONFeature, SiteAnalysis } from "@/lib/types";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

export default function AnalysisPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { project, summaryStats, loading, error, load } = useProjectData(projectId);
  const [analysis, setAnalysis] = useState<SiteAnalysis | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .getOptional<SiteAnalysis>(`/api/projects/${projectId}/site-analysis`)
      .then((data) => {
        if (!cancelled) setAnalysis(data);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const run = async () => {
    setRunning(true);
    setRunError("");
    try {
      setAnalysis(await api.post<SiteAnalysis>(`/api/projects/${projectId}/site-analysis`));
      load();
    } catch (e) {
      setRunError(String(e instanceof Error ? e.message : e));
    } finally {
      setRunning(false);
    }
  };

  const analysisFeatures = useMemo(() => {
    const roadFeatures = analysis?.nearby_roads_json?.features ?? [];
    const buildingFeatures = analysis?.existing_buildings_json?.features ?? [];
    return [...roadFeatures, ...buildingFeatures] as GeoJSONFeature[];
  }, [analysis?.nearby_roads_json, analysis?.existing_buildings_json]);

  const roads = analysis?.nearby_roads_json?.features ?? [];
  const buildings = analysis?.existing_buildings_json?.features ?? [];

  if (loading) return <ProjectLoading />;
  if (error || !project) return <ProjectError error={error || "Not found"} onRetry={load} />;

  const namedRoads = [
    ...new Set(roads.map((r) => String(r.properties?.name || "")).filter(Boolean)),
  ];
  const center: [number, number] = [project.center_lng ?? 77.5946, project.center_lat ?? 12.9716];
  const risks = analysis?.risks_json ?? [];

  return (
    <ProjectResultShell projectId={projectId} stats={summaryStats} flush>
      <div className="flex flex-1 flex-col lg:flex-row min-h-0">
        <div className="lg:w-[400px] xl:w-[420px] shrink-0 border-b lg:border-b-0 lg:border-r border-border bg-background-secondary/95 p-4 sm:p-5 space-y-4 overflow-y-auto">
          <ResultPageHeader
            title="Site Analysis"
            subtitle="Terrain, road proximity, boundary context, and planning risks."
            status={analysis ? undefined : "Not run"}
            statusVariant={analysis ? "accent" : "muted"}
          />

          <Button
            onClick={run}
            disabled={running}
            className="w-full gap-2 "
          >
            <ScanSearch className="h-4 w-4" />
            {running ? "Analyzing site…" : "Run Site Analysis"}
          </Button>

          {runError && <p className="text-xs text-[#F87171]">{runError}</p>}

          {!analysis && !running && (
            <GlassCard className="p-6">
              <EmptyState
                icon={Mountain}
                title="Run site analysis"
                description="Detect terrain, roads, nearby features, and risks. Draw a boundary on the map first for best results."
              />
            </GlassCard>
          )}

          {analysis && (
            <>
              <div className="grid grid-cols-2 gap-2">
                <MetricCard label="Area" value={formatArea(analysis.area_sqm ?? 0)} />
                <MetricCard label="Perimeter" value={formatDistance(analysis.perimeter_m ?? 0)} />
                <MetricCard label="Elev. min" value={`${analysis.elevation_min_m ?? "—"}`} unit="m" icon={Mountain} />
                <MetricCard label="Elev. max" value={`${analysis.elevation_max_m ?? "—"}`} unit="m" icon={Mountain} />
                <MetricCard label="Slope est." value={`${analysis.slope_percent_estimate ?? "—"}`} unit="%" />
                <MetricCard label="Roads nearby" value={String(roads.length)} icon={Route} />
              </div>

              {namedRoads.length > 0 && (
                <GlassCard className="p-3">
                  <h3 className="text-xs font-semibold text-foreground mb-2 flex items-center gap-1.5">
                    <Route className="h-3.5 w-3.5 text-accent" />
                    Nearby roads
                  </h3>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {namedRoads.slice(0, 8).map((r) => (
                      <li key={r}>• {r}</li>
                    ))}
                  </ul>
                </GlassCard>
              )}

              <GlassCard className="p-3">
                <h3 className="text-xs font-semibold text-foreground mb-2 flex items-center gap-1.5">
                  <TriangleAlert className="h-3.5 w-3.5 text-[#F59E0B]" />
                  Risks & warnings
                </h3>
                <RiskList items={risks} emptyMessage="No critical issues detected in visual analysis." />
              </GlassCard>

              <GlassCard className="p-3 text-[10px] text-muted-foreground space-y-1">
                <p className="flex items-center gap-1.5">
                  <Building2 className="h-3 w-3" />
                  Buildings detected: {buildings.length}
                </p>
                <p className="flex items-center gap-1.5">
                  <MapPin className="h-3 w-3" />
                  OSM/satellite context may be incomplete. Verify with survey/LiDAR/RTK data.
                </p>
              </GlassCard>
            </>
          )}
        </div>

        <div className="flex-1 relative min-h-[360px] bg-background">
          <MapView
            center={center}
            zoom={15}
            basemap="satellite"
            boundary={project.boundary_geojson}
            alignment={project.alignment_geojson}
            analysisFeatures={analysisFeatures}
            roadFeatures={roads as GeoJSONFeature[]}
            buildingFeatures={buildings as GeoJSONFeature[]}
            hideFloatingTools
          />

          <div className="absolute bottom-3 left-3 z-10 pointer-events-none">
            <GlassCard className="px-3 py-2 text-[10px] space-y-1 pointer-events-none">
              <p className="text-muted-foreground font-semibold uppercase tracking-wide">Legend</p>
              <p className="text-muted-foreground"><span className="inline-block w-2 h-2 rounded-full bg-[#10B981] mr-1.5" />Selected boundary</p>
              <p className="text-muted-foreground"><span className="inline-block w-2 h-2 rounded-full bg-accent mr-1.5" />Nearby road</p>
              <p className="text-muted-foreground"><span className="inline-block w-2 h-2 rounded-full bg-[#F59E0B] mr-1.5" />Risk zone</p>
              <p className="text-muted-foreground"><span className="inline-block w-2 h-2 rounded-full bg-[#94A3B8] mr-1.5" />Existing building</p>
            </GlassCard>
          </div>

          <div className="absolute bottom-3 right-3 z-10 font-mono text-[10px] text-muted-foreground pointer-events-none">
            {center[1].toFixed(5)}°, {center[0].toFixed(5)}°
          </div>
        </div>
      </div>
    </ProjectResultShell>
  );
}
