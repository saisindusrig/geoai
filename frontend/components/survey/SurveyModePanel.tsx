"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { SidebarMetricChip, SidebarStatusCard } from "@/components/layout/SidebarStatusCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api, uploadSurveyFile } from "@/lib/api";
import type {
  EngineeringLayer,
  GroundControlPoint,
  SiteAnalysis,
  SurveyDataset,
  SurveyStatus,
  ValidationReport,
} from "@/lib/types";
import AccuracyBadge from "./AccuracyBadge";
import EngineeringLayerPanel from "./EngineeringLayerPanel";
import OffsetCorrectionTool from "./OffsetCorrectionTool";
import SurveyLayerToggles from "./SurveyLayerToggles";

interface Props {
  projectId: number;
  onStatusChange?: (status: SurveyStatus) => void;
  onDataLoaded?: (layers: EngineeringLayer[], gcps: GroundControlPoint[]) => void;
}

const VECTOR_FORMATS = new Set(["geojson", "shapefile", "dxf"]);

export default function SurveyModePanel({ projectId, onStatusChange, onDataLoaded }: Props) {
  const [status, setStatus] = useState<SurveyStatus | null>(null);
  const [layers, setLayers] = useState<EngineeringLayer[]>([]);
  const [datasets, setDatasets] = useState<SurveyDataset[]>([]);
  const [gcps, setGcps] = useState<GroundControlPoint[]>([]);
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [accuracyReports, setAccuracyReports] = useState<
    { id: number; tier_result: string; passed: boolean; created_at: string }[]
  >([]);
  const [adjustment, setAdjustment] = useState<ValidationReport["gcp_adjustment"] | null>(null);
  const [importFormat, setImportFormat] = useState("geojson");
  const [layerType, setLayerType] = useState("road_centerline");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [gcpName, setGcpName] = useState("");
  const [gcpLng, setGcpLng] = useState("");
  const [gcpLat, setGcpLat] = useState("");
  const [designElevation, setDesignElevation] = useState("");
  const [cutFillResult, setCutFillResult] = useState<Record<string, unknown> | null>(null);

  const refresh = useCallback(async () => {
    const [st, ly, ds, gp, adj, reports] = await Promise.all([
      api.get<SurveyStatus>(`/api/projects/${projectId}/survey/status`),
      api.get<EngineeringLayer[]>(`/api/projects/${projectId}/survey/layers`),
      api.get<SurveyDataset[]>(`/api/projects/${projectId}/survey/datasets`),
      api.get<GroundControlPoint[]>(`/api/projects/${projectId}/survey/gcp`),
      api.get<ValidationReport["gcp_adjustment"]>(`/api/projects/${projectId}/survey/gcp/adjustment`).catch(() => null),
      api
        .get<{ id: number; tier_result: string; passed: boolean; created_at: string }[]>(
          `/api/projects/${projectId}/survey/accuracy-reports`,
        )
        .catch(() => []),
    ]);
    setStatus(st);
    setLayers(ly);
    setDatasets(ds);
    setGcps(gp);
    setAdjustment(adj);
    setAccuracyReports(reports);
    onStatusChange?.(st);
    onDataLoaded?.(ly, gp);
  }, [projectId, onStatusChange, onDataLoaded]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      void refresh()
        .catch(() => setError("Survey API unavailable"))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refresh]);

  const enableSurveyMode = async () => {
    setBusy(true);
    setError("");
    try {
      await api.post(`/api/projects/${projectId}/survey/mode`, { enabled: true });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to enable Survey Mode");
    } finally {
      setBusy(false);
    }
  };

  const disableSurveyMode = async () => {
    setBusy(true);
    setError("");
    try {
      await api.post(`/api/projects/${projectId}/survey/mode`, { enabled: false });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to disable Survey Mode");
    } finally {
      setBusy(false);
    }
  };

  const onImport = async (file: File) => {
    setBusy(true);
    setError("");
    try {
      await uploadSurveyFile(projectId, file, {
        format: importFormat,
        layer_type: layerType,
        name: file.name,
        kind: importFormat === "geotiff" ? "dem" : "vector",
      });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setBusy(false);
    }
  };

  const importOsmContext = async () => {
    setBusy(true);
    setError("");
    try {
      let analysis = await api.getOptional<SiteAnalysis>(`/api/projects/${projectId}/site-analysis`);
      if (!analysis?.raw_geojson) {
        analysis = await api.post<SiteAnalysis>(`/api/projects/${projectId}/site-analysis`);
      }
      const geojson = analysis.raw_geojson ?? analysis.nearby_roads_json;
      if (!geojson) {
        setError("No OSM features available — set a site location first.");
        return;
      }
      await api.post(`/api/projects/${projectId}/survey/import/osm-context`, geojson);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "OSM import failed");
    } finally {
      setBusy(false);
    }
  };

  const createGcp = async () => {
    const lng = parseFloat(gcpLng);
    const lat = parseFloat(gcpLat);
    if (!gcpName.trim() || Number.isNaN(lng) || Number.isNaN(lat)) {
      setError("Enter GCP name, longitude, and latitude.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.post(`/api/projects/${projectId}/survey/gcp`, {
        name: gcpName.trim(),
        lng,
        lat,
        source: "manual",
      });
      setGcpName("");
      setGcpLng("");
      setGcpLat("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "GCP create failed");
    } finally {
      setBusy(false);
    }
  };

  const runCutFill = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await api.post<Record<string, unknown>>(`/api/projects/${projectId}/survey/cut-fill`, {
        design_elevation_m: designElevation ? parseFloat(designElevation) : null,
        road_width_m: 7,
      });
      setCutFillResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Cut/fill analysis failed");
    } finally {
      setBusy(false);
    }
  };

  const runValidation = async () => {
    setBusy(true);
    try {
      const report = await api.post<ValidationReport>(`/api/projects/${projectId}/survey/validate`);
      setValidation(report);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setBusy(false);
    }
  };

  const activeAdjustment = validation?.gcp_adjustment ?? adjustment;
  const passedCount = validation ? validation.checks.filter((c) => c.passed).length : 0;
  const failedChecks = validation?.checks.filter((c) => !c.passed) ?? [];

  if (loading && !status) {
    return (
      <SidebarStatusCard title="Survey">
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          Loading…
        </div>
      </SidebarStatusCard>
    );
  }

  return (
    <SidebarStatusCard
      title="Survey"
      trailing={status ? <AccuracyBadge tier={status.accuracy_tier} compact /> : null}
    >
      {!status?.postgis_available && (
        <p className="text-[10px] text-warning leading-snug rounded-md border border-warning/25 bg-warning/5 px-2 py-1">
          PostGIS required — start Docker for full survey mode.
        </p>
      )}

      {error && <p className="text-[10px] text-destructive">{error}</p>}

      {!status?.survey_mode_enabled ? (
        <Button
          size="sm"
          className="w-full h-8 text-xs"
          disabled={busy || !status?.postgis_available}
          onClick={enableSurveyMode}
        >
          Enable Survey Mode
        </Button>
      ) : (
        <div className="space-y-2">
          <div className="flex gap-1">
            <SidebarMetricChip label="Layers" value={layers.length} />
            <SidebarMetricChip label="Data" value={datasets.length} />
            <SidebarMetricChip label="GCPs" value={gcps.length} />
          </div>

          {status.engineering_crs_epsg && (
            <div className="rounded-md border border-border/50 bg-muted/10 px-2 py-1.5 text-[10px] text-muted-foreground">
              <p className="font-semibold text-foreground">Engineering CRS</p>
              <p>EPSG:{status.engineering_crs_epsg}</p>
            </div>
          )}

          <Button
            size="sm"
            variant="outline"
            className="w-full h-7 text-xs"
            disabled={busy}
            onClick={disableSurveyMode}
          >
            Disable Survey Mode
          </Button>

          <SurveyLayerToggles compact />

          <div className="space-y-1.5 rounded-md border border-border/50 bg-muted/10 p-2">
            <p className="text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">Import</p>
            <Select
              value={importFormat}
              onChange={(e) => setImportFormat(e.target.value)}
              className="h-7 text-xs px-2 w-full"
            >
              <option value="geojson">GeoJSON</option>
              <option value="shapefile">Shapefile (.zip)</option>
              <option value="geotiff">GeoTIFF DEM/Ortho</option>
              <option value="gcp_csv">GCP CSV</option>
              <option value="las">LAS/LAZ</option>
              <option value="dxf">DXF</option>
            </Select>
            {VECTOR_FORMATS.has(importFormat) && (
              <Select
                value={layerType}
                onChange={(e) => setLayerType(e.target.value)}
                className="h-7 text-xs px-2 w-full"
              >
                <option value="road_centerline">Road centerline</option>
                <option value="pipeline_centerline">Pipeline centerline</option>
                <option value="site_boundary">Site boundary</option>
                <option value="building_footprint">Building footprint</option>
              </Select>
            )}
            <Input
              type="file"
              className="h-7 text-[10px]"
              disabled={busy}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void onImport(f);
              }}
            />
            <Button
              size="sm"
              variant="secondary"
              className="w-full h-7 text-xs"
              disabled={busy}
              onClick={importOsmContext}
            >
              Import OSM context
            </Button>
          </div>

          <div className="space-y-1.5 rounded-md border border-border/50 bg-muted/10 p-2">
            <p className="text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">Add GCP</p>
            <Input
              placeholder="Name"
              value={gcpName}
              onChange={(e) => setGcpName(e.target.value)}
              className="h-7 text-xs"
            />
            <div className="grid grid-cols-2 gap-1">
              <Input
                placeholder="Lng"
                value={gcpLng}
                onChange={(e) => setGcpLng(e.target.value)}
                className="h-7 text-xs font-data"
              />
              <Input
                placeholder="Lat"
                value={gcpLat}
                onChange={(e) => setGcpLat(e.target.value)}
                className="h-7 text-xs font-data"
              />
            </div>
            <Button size="sm" className="w-full h-7 text-xs" disabled={busy} onClick={createGcp}>
              Create GCP
            </Button>
          </div>

          {layers.length > 0 && (
            <div className="space-y-1">
              <p className="text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
                Layers ({layers.length})
              </p>
              <EngineeringLayerPanel layers={layers} compact />
            </div>
          )}

          {activeAdjustment && (
            <OffsetCorrectionTool
              projectId={projectId}
              adjustment={activeAdjustment}
              onApplied={refresh}
              compact
            />
          )}

          <div className="space-y-1.5 rounded-md border border-border/50 bg-muted/10 p-2">
            <p className="text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">Cut / fill</p>
            <Input
              placeholder="Design elevation (m, optional)"
              value={designElevation}
              onChange={(e) => setDesignElevation(e.target.value)}
              className="h-7 text-xs font-data"
            />
            <Button size="sm" variant="secondary" className="w-full h-7 text-xs" disabled={busy} onClick={runCutFill}>
              Run cut/fill
            </Button>
            {cutFillResult && (
              <p className="text-[10px] text-muted-foreground">
                Cut {(cutFillResult.cut_m3 as number | undefined)?.toLocaleString?.() ?? "—"} m³ · Fill{" "}
                {(cutFillResult.fill_m3 as number | undefined)?.toLocaleString?.() ?? "—"} m³
              </p>
            )}
          </div>

          <Button
            size="sm"
            variant="outline"
            className="w-full h-7 text-xs"
            disabled={busy}
            onClick={runValidation}
          >
            Run validation
          </Button>

          {validation && (
            <div className="text-[10px] space-y-1 border-t border-border/50 pt-1.5">
              <p className="text-muted-foreground">
                {passedCount}/{validation.checks.length} checks passed
                {failedChecks.length > 0 && ` · ${failedChecks.length} issues`}
              </p>
              {failedChecks.slice(0, 2).map((c) => (
                <p key={c.id} className="text-warning line-clamp-2">
                  {c.label}
                </p>
              ))}
            </div>
          )}

          {accuracyReports.length > 0 && (
            <div className="text-[10px] space-y-1 border-t border-border/50 pt-1.5">
              <p className="font-semibold text-muted-foreground">Accuracy reports</p>
              {accuracyReports.slice(0, 3).map((r) => (
                <p key={r.id} className="text-muted-foreground">
                  {r.tier_result} · {r.passed ? "passed" : "failed"} ·{" "}
                  {new Date(r.created_at).toLocaleDateString()}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </SidebarStatusCard>
  );
}
