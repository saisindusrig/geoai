import type { EditableModelComponent, EditableModelDocument } from "@/lib/types";

/** Curated identity fields shared by all workspace inspectors. */
export default function ComponentIdentity({ component, document }: { component: EditableModelComponent; document?: EditableModelDocument | null }) {
  const placement = document?.metadata.placementProvenance as Record<string, unknown> | undefined;
  const patch = component.metadata?.patchProvenance as Record<string, unknown> | undefined;
  const fields = [
    ["Component ID", component.id],
    ["Kind", component.metadata?.componentKind],
    ["Role", component.metadata?.componentRole],
    ["Asset", component.metadata?.assetId],
    ["Building ID", component.metadata?.buildingId],
    ["Floor", component.metadata?.floor],
    ["Source component", component.metadata?.sourceComponentId],
    ["Specification", component.metadata?.specificationId],
    ["Proposal", component.metadata?.proposalVersionId],
    ["Source revision", component.metadata?.sourceModelRevisionId],
    ["Patch operation", patch?.patchOperationId],
    ["Patch source revision", patch?.sourceModelRevisionId],
    ["Placement", placement?.placement_state],
    ["Elevation resolution", placement?.elevation_resolution],
  ];
  return <dl aria-label="Component identity" className="space-y-1 text-[10px]">
    {document && document.origin.elevation_m == null && <p>Elevation unknown · local visual reference only</p>}
    {fields.filter(([, value]) => typeof value === "string" || typeof value === "number").map(([label, value]) =>
      <div key={String(label)}><dt className="text-muted-foreground">{String(label)}</dt><dd className="break-all">{String(value)}</dd></div>)}
  </dl>;
}
