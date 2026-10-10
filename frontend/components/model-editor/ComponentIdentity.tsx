import type { EditableModelComponent, EditableModelDocument } from "@/lib/types";

/** Curated identity fields shared by all workspace inspectors. */
export default function ComponentIdentity({ component, document }: { component: EditableModelComponent; document?: EditableModelDocument | null }) {
  const placement = document?.metadata.placementProvenance as Record<string, unknown> | undefined;
  const patch = component.metadata?.patchProvenance as Record<string, unknown> | undefined;
  const fields = [
    ["Component ID", component.id],
    ["BIM component", component.metadata?.componentId],
    ["Assembly", component.metadata?.assemblyId],
    ["CAD geometry", component.metadata?.geometryStatus],
    ["Design", component.metadata?.designId],
    ["Design version", component.metadata?.designVersion],
    ["Material", component.metadata?.materialId],
    ["Engineering", component.metadata?.engineeringStatus],
    ["CAD proposal", component.metadata?.cadProposalVersionId],
    ["Kind", component.metadata?.componentKind],
    ["Role", component.metadata?.componentRole],
    ["Asset", component.metadata?.assetId],
    ["3D design", component.metadata?.ai3dDesignId],
    ["System", component.metadata?.systemId],
    ["Primitive", component.metadata?.primitiveType],
    ["Source object", component.metadata?.sourceObjectId],
    ["Executor", component.metadata?.executorVersion],
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
    {component.geometry?.kind === "cad_mesh" && <>
      <dt className="text-muted-foreground">Authoritative component parameters</dt>
      <dd>{Object.entries((component.metadata?.parameters ?? {}) as Record<string, number>).map(([name,value]) => <p key={name}>{name}: {value} m</p>)}</dd>
      <dt className="text-muted-foreground">Preview assumptions</dt>
      <dd>{((component.metadata?.previewAssumptions ?? []) as string[]).map(statement => <p key={statement}>{statement}</p>)}</dd>
      <dd>Rigid transforms only. Shape/material edits require reviewed parametric regeneration.</dd>
    </>}
  </dl>;
}
