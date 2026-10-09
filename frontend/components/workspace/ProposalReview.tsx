"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import type { ProposalView, ApplicationApproval } from "@/lib/generated/stage1";

export default function ProposalReview({ projectId, versionId }: { projectId: number; versionId: string }) {
  const base = `/api/projects/${projectId}`;
  const [proposal, setProposal] = useState<ProposalView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reviewed, setReviewed] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const [alternative, setAlternative] = useState<string | null>(null);
  const load = () => api.get<ProposalView>(`${base}/proposals/versions/${versionId}`).then(setProposal);
  useEffect(() => {
    let live = true;
    api.get<ProposalView>(`${base}/proposals/versions/${versionId}`).then(p => { if (live) setProposal(p); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [base, versionId]);
  const act = async (action: "approve" | "reject") => {
    if (!proposal) return;
    setBusy(true); setError(null);
    try {
      if (action === "approve") {
        const body: ApplicationApproval = { clientRequestId: `approve-${versionId}`, proposalVersionId: versionId,
          proposalHash: proposal.contentHash, dependencyHash: proposal.dependencyHash, validationHash: proposal.validationHash,
          alternativeId: alternative, acknowledgedAssumptionVersionIds: proposal.content.contract.assumptionVersionIds,
          expectedModelRevisionId: proposal.content.context.modelRevisionId ?? null };
        await api.post(`${base}/proposals/approve`, body);
      } else await api.post(`${base}/proposals/versions/${versionId}/reject`);
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Proposal action failed."); }
    finally { setBusy(false); }
  };
  return <section aria-label="Proposal review" className="space-y-2 rounded border border-border p-2">
    {error && <p role="alert">{error}</p>}
    {!proposal ? <Button size="sm" onClick={() => void load().catch(e => setError(e.message))}>Load proposal</Button> : <>
      <p className="font-semibold">{proposal.content.request.title} · v{proposal.version}</p>
      <p>{proposal.status} · Concept only</p>
      <Button size="sm" variant="secondary" onClick={() => setReviewed(!reviewed)}>{reviewed ? "Close review" : "Review proposal"}</Button>
      {reviewed && <>
        <p>{proposal.content.request.rationale}</p>
        {proposal.content.request.assets.map((a, i) => <p key={i}>{a.name} · {a.assetType}: {a.requirements?.join("; ") || "Concept requirements to be confirmed"}</p>)}
        {proposal.content.assetProposals?.map(a => <div key={a.assetRequestId} className="rounded border border-border p-2">
          <p>{a.displayName} · {a.assetFamily} · {a.proposalState}</p>
          <p>Generation: {a.generationEligible ? "Eligible for specialist review" : "Unavailable"}</p>
          {a.blockers.map((b, i) => <p key={i}>{b}</p>)}
        </div>)}
        {proposal.status !== "REJECTED" && proposal.content.preview && <div aria-label="Temporary proposal preview" className="border border-dashed border-amber-500 p-2 text-amber-300">
          <p>PREVIEW ONLY · saved model unchanged</p>
          <p>Translate {proposal.content.preview.objectIds.join(", ")} · Local XYZ {proposal.content.preview.deltaM.join(", ")} m</p>
          <p>Affected connections require specialist review; they have not been inferred.</p>
        </div>}
        {proposal.content.request.warnings?.map((w, i) => <p key={`w-${i}`}>Warning: {w}</p>)}
        {proposal.validation?.issues.map((issue, i) => <p key={`v-${i}`}>{issue.severity}: {issue.message}</p>)}
        {proposal.content.request.assumptions?.map((a, i) => <p key={`a-${i}`}>Assumption: {a}</p>)}
        {!!proposal.alternatives.length && <label>Alternative<select aria-label="Proposal alternative" value={alternative ?? ""} onChange={e => setAlternative(e.target.value || null)} className="w-full bg-background p-2"><option value="">Select an alternative</option>{proposal.alternatives.map(a => <option key={a.id} value={a.id}>{a.name}: {a.payload.rationale}</option>)}</select></label>}
        <label className="flex gap-2"><input type="checkbox" checked={acknowledged} onChange={e => setAcknowledged(e.target.checked)} />I reviewed the assumptions, warnings and conceptual scope.</label>
        <div className="flex gap-2">
          <Button size="sm" disabled={busy || !acknowledged || proposal.status !== "READY_FOR_REVIEW" || !!proposal.alternatives.length && !alternative} onClick={() => void act("approve")}>Approve proposal</Button>
          <Button size="sm" variant="secondary" disabled={busy || !["READY_FOR_REVIEW", "HAS_ISSUES"].includes(proposal.status)} onClick={() => void act("reject")}>Reject proposal</Button>
        </div>
        <p className="text-muted-foreground">Approval records concept review. Generation is not available in this batch.</p>
      </>}
    </>}
  </section>;
}
