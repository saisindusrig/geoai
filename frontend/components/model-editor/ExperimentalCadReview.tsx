"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { EditableModelEditor } from "@/hooks/useEditableModelEditor";

type Review = {snapshotHash: string; componentIds: string[];
  components: {id:string;assembly:string;recipe:string;parameters:Record<string,number>;material:string}[];
  proposal: {
  id: string; contentHash: string; dependencyHash: string; validationHash: string;
  content: {contract: {assumptionVersionIds: string[]}; context: {modelRevisionId: string}};
}};

export default function ExperimentalCadReview({editor, projectId}: {editor: EditableModelEditor; projectId?: number}) {
  const [enabled, setEnabled] = useState(false);
  const [review, setReview] = useState<Review | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    if (projectId) api.get(`/api/projects/${projectId}/experimental-cad/capability`).then(() => {if(active) setEnabled(true);}).catch(() => {if(active) setEnabled(false);});
    return () => {active = false;};
  }, [projectId]);
  if (!enabled || !projectId || !editor.baseRevision) return null;
  const root = `/api/projects/${projectId}/experimental-cad`;
  const prepare = async (beamLength: number) => {
    setBusy(true); setError(null); setAcknowledged(false);
    try {setReview(await api.post<Review>(`${root}/support-frame/review`, {
      request_id: crypto.randomUUID(), scenario_id: editor.baseRevision!.scenario_id,
      expected_revision_id: editor.baseRevision!.id, beam_length: beamLength,
    }));} catch(reason) {setError(reason instanceof Error ? reason.message : String(reason));} finally {setBusy(false);}
  };
  const execute = async () => {
    if (!review || !acknowledged || editor.dirty) return;
    setBusy(true); setError(null);
    try {
      const p = review.proposal;
      await api.post(`${root}/approve`, {clientRequestId: crypto.randomUUID(), proposalVersionId: p.id,
        proposalHash: p.contentHash, dependencyHash: p.dependencyHash, validationHash: p.validationHash,
        alternativeId: null, acknowledgedAssumptionVersionIds: p.content.contract.assumptionVersionIds,
        expectedModelRevisionId: p.content.context.modelRevisionId});
      await api.post(`${root}/reviews/${p.id}/execute`, {});
      window.location.reload();
    } catch(reason) {setError(reason instanceof Error ? reason.message : String(reason));} finally {setBusy(false);}
  };
  return <details className="border-b border-border p-3 text-xs"><summary>Experimental CAD review</summary>
    <p className="my-2">Private native geometry · production CAD Build disabled. Structural adequacy, terrain, foundations, loads and code compliance remain unverified.</p>
    <button disabled={busy || editor.dirty} onClick={() => prepare(5)}>Review SUPPORT_FRAME · 5 m</button>
    {editor.document?.metadata.cadCatalogId != null && <button className="ml-3" disabled={busy || editor.dirty} onClick={() => prepare(6)}>Review beam change · 6 m</button>}
    {editor.dirty && <p>Save your current edits before requesting a CAD review.</p>}
    {review && <div className="mt-2 space-y-2"><p>{review.componentIds.length} components · source revision {review.proposal.content.context.modelRevisionId}</p><p className="break-all">Snapshot {review.snapshotHash}</p>
      <details><summary>Reviewed component definitions · metres</summary>{review.components.map(c=><div key={c.id} className="my-2"><strong>{c.id}</strong><p>Assembly {c.assembly} · {c.recipe} · {c.material}</p><p>{Object.entries(c.parameters).map(([name,value])=>`${name}: ${value}`).join(" · ")}</p></div>)}</details>
      <p>Support/slab clearances require review; clearance rules are unavailable. No supports will be repositioned.</p><label className="block"><input type="checkbox" checked={acknowledged} onChange={event => setAcknowledged(event.target.checked)} /> I reviewed this exact snapshot and acknowledge its preview assumptions and unverified engineering status.</label><button disabled={!acknowledged || busy || editor.dirty} onClick={execute}>{busy ? "Executing bounded CAD worker…" : "Explicitly approve and compile experimental CAD"}</button></div>}
    {error && <p role="alert">{error}</p>}
  </details>;
}
