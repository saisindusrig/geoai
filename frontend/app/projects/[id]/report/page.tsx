"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Box,
  Calendar,
  FileJson,
  FileSpreadsheet,
  FileText,
  Layers,
  Mountain,
  Ruler,
} from "lucide-react";
import { ProjectError, ProjectLoading } from "@/components/layout/ProjectHeader";
import ExportCard from "@/components/project-results/ExportCard";
import ProjectResultShell from "@/components/project-results/ProjectResultShell";
import ResultPageHeader from "@/components/project-results/ResultPageHeader";
import RiskList from "@/components/project-results/RiskList";
import EmptyState from "@/components/ui/empty-state";
import { GlassCard } from "@/components/ui/glass-card";
import { Input } from "@/components/ui/input";
import ProjectValidationPanel from "@/components/project/ProjectValidationPanel";
import { useProjectData } from "@/hooks/useProjectData";
import { api, apiUrl } from "@/lib/api";
import type { SurveyStatus } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";

const EXPORTS = [
  { id: "pdf", label: "Download PDF Report", desc: "Full preliminary planning report with assumptions", icon: FileText, preview: "Executive summary, BOQ snapshot, risks", fileType: "PDF" },
  { id: "csv", label: "Download Excel BOQ", desc: "Bill of quantities spreadsheet (CSV)", icon: FileSpreadsheet, preview: "Line items, rates, quantities", fileType: "CSV" },
  { id: "dxf", label: "Download DXF", desc: "CAD exchange format for site layout", icon: Ruler, preview: "Boundary and alignment linework", fileType: "DXF" },
  { id: "json", label: "Download Project Data", desc: "Complete structured JSON export", icon: FileJson, preview: "Parameters, geometry, estimates", fileType: "JSON" },
  { id: "geojson", label: "Download GeoJSON", desc: "Boundary, alignment & site layers", icon: FileJson, preview: "GIS-compatible site data", fileType: "GeoJSON" },
] as const;

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { project, design, summaryStats, loading, error, load, modelFile, calc, estimate, scenario } =
    useProjectData(projectId);
  const serverAssumptions = scenario?.assumptions_json ?? [];
  const [editing, setEditing] = useState(false);
  const [draftAssumptions, setDraftAssumptions] = useState<string[]>([]);
  const [showPdfPreview, setShowPdfPreview] = useState(false);
  const [surveyStatus, setSurveyStatus] = useState<SurveyStatus | null>(null);
  const assumptions = editing ? draftAssumptions : serverAssumptions;

  useEffect(() => {
    api
      .getOptional<SurveyStatus>(`/api/projects/${projectId}/survey/status`)
      .then(setSurveyStatus)
      .catch(() => setSurveyStatus(null));
  }, [projectId]);

  const saveAssumptions = async () => {
    if (!scenario) return;
    await api.put(`/api/projects/${projectId}/scenarios/${scenario.id}/assumptions`, {
      assumptions: draftAssumptions,
    });
    setEditing(false);
    await load();
  };

  if (loading) return <ProjectLoading />;
  if (error || !project) return <ProjectError error={error || "Not found"} onRetry={load} />;

  const cost = calc?.cost_summary;
  const timeline = calc?.timeline;

  return (
    <ProjectResultShell projectId={projectId} stats={summaryStats} maxWidth="max-w-6xl">
      <ResultPageHeader
        title="Reports & Export Center"
        subtitle="Download preliminary reports, BOQ, models, and project data."
      />

      <ProjectValidationPanel projectId={projectId} className="mb-1" />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {EXPORTS.map(({ id, label, desc, icon, preview, fileType }) => (
          <ExportCard
            key={id}
            title={label}
            description={desc}
            preview={preview}
            fileType={fileType}
            icon={icon}
            href={id === "dxf" ? undefined : apiUrl(`/api/projects/${projectId}/exports/${id}`)}
            available={id === "dxf" ? false : !!design || id === "json" || id === "geojson"}
            unavailableReason={
              id === "dxf"
                ? "DXF export is planned — use GeoJSON or GLB for now."
                : !design
                  ? "Generate a design in AI Design Studio first."
                  : undefined
            }
            onPreview={id === "pdf" ? () => setShowPdfPreview(true) : undefined}
          />
        ))}

        {surveyStatus?.survey_mode_enabled && (
          <>
            <ExportCard
              title="Survey terrain GLB"
              description="Engineering terrain mesh from survey DEM"
              fileType="GLB"
              icon={Mountain}
              href={apiUrl(`/api/projects/${projectId}/exports/terrain.glb`)}
              available={surveyStatus.postgis_available}
              unavailableReason="Requires PostGIS and survey-grade DEM."
            />
            <ExportCard
              title="Survey roads GLB"
              description="Engineering centerline mesh export"
              fileType="GLB"
              icon={Layers}
              href={apiUrl(`/api/projects/${projectId}/exports/roads.glb`)}
              available={surveyStatus.postgis_available}
              unavailableReason="Requires PostGIS and imported vectors."
            />
            <ExportCard
              title="Accuracy report"
              description="Latest survey validation JSON"
              fileType="JSON"
              icon={FileJson}
              href={apiUrl(`/api/projects/${projectId}/exports/accuracy-report.json`)}
              available={surveyStatus.postgis_available}
              unavailableReason="Run survey validation first."
            />
          </>
        )}

        <ExportCard
          title="Download 3D Model"
          description={modelFile ? "Conceptual GLB for BIM review" : "Generate a design first"}
          fileType="GLB"
          icon={Box}
          href={modelFile?.file_url ?? undefined}
          available={!!modelFile}
          unavailableReason="Generate a design to export the 3D model."
        />

        <Link href={`/projects/${projectId}/timeline`} className="block h-full">
          <ExportCard
            title="Construction Timeline"
            description="View sequence and export from Timeline page"
            fileType="JSON"
            icon={Calendar}
            available={!!design}
            unavailableReason="Generate a design to view timeline."
          />
        </Link>
      </div>

      {showPdfPreview && (
        <GlassCard className="overflow-hidden">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <h3 className="text-sm font-semibold text-foreground">PDF report preview</h3>
            <button type="button" className="text-xs text-muted-foreground hover:text-foreground" onClick={() => setShowPdfPreview(false)}>
              Close
            </button>
          </div>
          <iframe
            title="PDF preview"
            src={apiUrl(`/api/projects/${projectId}/exports/pdf`)}
            className="w-full h-[480px] bg-background border-0"
          />
        </GlassCard>
      )}

      {design ? (
        <GlassCard className="p-4 sm:p-6 space-y-5">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Report preview</h3>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{design.summary}</p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <PreviewSection title="Executive summary" body={design.summary} />
            <PreviewSection
              title="Quantity snapshot"
              body={
                estimate
                  ? `Concrete ${estimate.concrete_m3} m³ · Steel ${estimate.steel_kg} kg · Cement ${estimate.cement_bags} bags`
                  : "BOQ available after estimate generation."
              }
            />
            <PreviewSection
              title="Cost summary"
              body={
                cost
                  ? `Medium ${formatCurrency(cost.total_medium, cost.currency)} (${formatCurrency(cost.total_low)} – ${formatCurrency(cost.total_high)})`
                  : "Cost summary pending."
              }
            />
            <PreviewSection
              title="Timeline summary"
              body={
                timeline
                  ? `~${timeline.estimated_months_medium} months (${timeline.estimated_months_low}–${timeline.estimated_months_high})`
                  : "Timeline pending."
              }
            />
          </div>

          <section>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-foreground">Assumptions</h4>
              {scenario && (
                <button
                  type="button"
                  onClick={() => {
                    if (editing) {
                      void saveAssumptions();
                    } else {
                      setDraftAssumptions([...serverAssumptions]);
                      setEditing(true);
                    }
                  }}
                  className="text-xs text-primary hover:underline"
                >
                  {editing ? "Save" : "Edit"}
                </button>
              )}
            </div>
            {editing ? (
              <div className="space-y-1.5">
                {assumptions.map((a, i) => (
                  <Input
                    key={i}
                    aria-label={`Assumption ${i + 1}`}
                    value={a}
                    onChange={(e) =>
                      setDraftAssumptions((prev) => prev.map((x, j) => (j === i ? e.target.value : x)))
                    }
                    className="h-8 text-xs bg-background-secondary/80 border-border"
                  />
                ))}
              </div>
            ) : (
              <ul className="text-xs text-muted-foreground list-disc pl-4 space-y-0.5">
                {assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h4 className="text-sm font-semibold text-foreground mb-2">Risk checklist</h4>
            <RiskList items={design.risks} />
          </section>

          <p className="text-[10px] text-muted-foreground border-t border-border pt-3">
            Preliminary AI planning only. Final construction drawings, quantities, and approvals must be verified by licensed engineers and survey data.
          </p>
        </GlassCard>
      ) : (
        <GlassCard className="p-8">
          <EmptyState
            title="No completed design yet"
            description="Generate one in AI Design Studio to unlock full report preview and exports."
          />
        </GlassCard>
      )}
    </ProjectResultShell>
  );
}

function PreviewSection({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-border bg-background/60 p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{title}</p>
      <p className="mt-1.5 text-xs leading-relaxed text-foreground-secondary line-clamp-4">{body}</p>
    </div>
  );
}
