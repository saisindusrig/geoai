"use client";

import { useEffect } from "react";
import { publishAssistantContext } from "@/lib/site-assistant";

type Props = { projectId: number; selectedIds: string[]; revisionId: number | null; dirty: boolean; siteGeometry?: import("@/lib/types").GeoJSONGeometry | null };

/** All previous entry points open the one root-mounted Nebius assistant. */
export default function PersistentAssistant({ projectId, selectedIds, revisionId, dirty }: Props) {
  const selection = selectedIds.join("\u0000");
  useEffect(() => { publishAssistantContext({ project_id: projectId, selected_ids: selection ? selection.split("\u0000") : [], revision_id: revisionId, dirty }); }, [projectId, selection, revisionId, dirty]);
  return <div className="space-y-3 p-4 text-sm"><p>The site-wide StruvoCivil Assistant uses Nebius with your current page and selection.</p><button className="underline" onClick={() => window.dispatchEvent(new Event("geoai:open-site-assistant"))}>Open StruvoCivil Assistant</button><p className="text-xs text-muted-foreground">Existing saved conversations remain available in Assistant history. Model changes and numerical analyses require review and approval in their existing tools.</p></div>;
}
