"use client";
import type { DesignOutput } from "@/lib/types";

interface Props {
  projectId: number;
  design?: DesignOutput | null;
  onApplyParameters: (params: Record<string, unknown>) => void;
  onRegenerate: (params: Record<string, unknown>) => void;
  onRunSiteAnalysis?: () => Promise<void>;
  currentParameters?: Record<string, unknown> | null;
}
export default function ModernAssistantPanel(_props: Props) {
  return <div className="p-4 text-sm"><p>Use the site-wide Nebius Assistant for project {_props.projectId}.</p><button className="mt-3 underline" onClick={() => window.dispatchEvent(new Event("geoai:open-site-assistant"))}>Open StruvoCivil Assistant</button></div>;
}
