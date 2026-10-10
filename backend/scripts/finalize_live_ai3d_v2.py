"""Read persisted acceptance evidence and write the final report; no AI calls."""
import json
import hashlib
from pathlib import Path
from live_ai3d_acceptance import save
from app.db.session import SessionLocal
from app.db.models import ModelRevision
from app.services.assistant.storage import rows

OUT=Path('live-results/universal-v2')

def main():
    cases=[json.loads((OUT/f'case-{c}.json').read_text(encoding='utf-8')) for c in 'ABC']
    audit=json.loads((OUT/'offline-review-and-build.json').read_text(encoding='utf-8'))
    completions=[r for c in cases for r in c['completions']]
    with SessionLocal() as db:
        generated=db.get(ModelRevision,32); manual=db.get(ModelRevision,33)
        if generated.project_id!=578 or manual.project_id!=578:raise RuntimeError('REVISION_PROJECT_GUARD')
        before={c['id']:c for c in generated.document_json['components']}
        after={c['id']:c for c in manual.document_json['components']}
        changed=[cid for cid in before if before[cid]!=after.get(cid)]
        proof={'providerCalls':0,'generatedRevision':32,'manualRevision':33,'manualSource':manual.source,
            'changedComponentIds':changed,'addedIds':sorted(after.keys()-before.keys()),'removedIds':sorted(before.keys()-after.keys()),
            'deckEastAfterReload':after['pedestrian-bridge-001:deck-001']['transform']['position'][0],
            'designIdentityPreserved':all(before[cid]['metadata']==after[cid]['metadata'] for cid in before),
            'lineage32':len([x for x in rows(db,'model_object_lineage',578) if x['model_revision_id']==32]),
            'lineage33':len([x for x in rows(db,'model_object_lineage',578) if x['model_revision_id']==33]),
            'browserTest':'1 passed (11.2s)',
            'visualReview':'Screenshot inspected: visible deck, three piers and end abutments; unknown elevation shown in Inspect. Existing Underground view used.',
            'screenshots':['backend/live-results/universal-v2/workspace-accepted.png']}
        save(OUT/'workspace-verification.json',proof)
    stats={'requests':len(completions),'http200':sum(r.get('httpStatus')==200 for r in completions),
        'validStructured':sum(bool(r.get('structuredValid')) for r in completions),
        'ordinaryRepairs':sum(r['ordinaryRepair'] for r in completions),'nestedRepairs':sum(r['nestedRepair'] for r in completions),
        'timeouts':sum(r['timeout'] for r in completions),'truncations':sum(r.get('finishReason')=='length' for r in completions),
        'inputTokens':sum(r.get('inputTokens') or 0 for r in completions),'outputTokens':sum(r.get('outputTokens') or 0 for r in completions),
        'completionLatencySeconds':round(sum(r['latencySeconds'] for r in completions),3),
        'flowLatencySeconds':round(sum(c['latencySeconds'] for c in cases),3)}
    frozen=[]
    for case in cases:
        original=json.loads((Path('live-results/universal-v1')/f"case-{case['case']}.json").read_text(encoding='utf-8'))
        frozen.append({'case':case['case'],'sameOriginalMessage':case['messageId']==original['messageId'],
            'sameFrozenContext':case['runContext']['context']==original['runContext']['context']})
    manifest={'statistics':stats,'frozenContextChecks':frozen,'files':[]}
    for path in sorted(OUT.glob('*.json')):
        if path.name=='verified-manifest.json':continue
        raw=path.read_bytes();json.loads(raw.decode('utf-8'))
        manifest['files'].append({'path':str(path.resolve()),'readable':True,'sha256':hashlib.sha256(raw).hexdigest()})
    save(OUT/'verified-manifest.json',manifest)
    report='''# Real Live GeoAI → 3D Acceptance V2

Decision: **NOT ACCEPTED as a complete live product flow.** A fresh bridge design built and passed real workspace editing acceptance, but all three Assistant runs ended FAILED. No runtime or model tuning was performed.

1. **Three flows executed:** A/project577, B/project578, C/project576. Original message IDs and frozen contexts were reused exactly; the manifest verifies equality. Fresh Qwen output was used for B. No additional case, model, connectivity test or benchmark ran.

2. **Completion requests:** 11: A=5, B=3, C=3. Only PRIMARY Qwen/Qwen3.5-397B-A17B. Existing temperature, 3,500 output tokens, tools and schemas were unchanged.

3. **Provider responses:** 11 HTTP 200 responses. Ten finish_reason=stop; one=length. Nine responses passed their requested structured schema; one nested repair failed argument schema and another response was truncated. HTTP success is not product-flow success.

4. **Ordinary repairs:** 0.

5. **Nested repairs:** 3 attempts, one per invalid call: A first repair passed schema; A second repair failed schema; C repair failed because the provider response truncated. No repair was retried manually.

6. **Timeouts:** 0. PRIMARY completion timeout remained 45s and overall flow deadline remained 120s.

7. **Truncation:** 1, C's nested repair, finish_reason=length, exactly 3,500 output tokens. Runtime terminal code TOOL_ARGUMENT_REPAIR_FAILED; captured underlying provider classification LIKELY_TRUNCATED/OUTPUT_LIMIT, cause INVALID_RESPONSE.

8. **AREA:** Classification WAREHOUSE, PARKING, ACCESS_ROAD. First repaired design had corresponding systems, with POLYGON, EXTRUDE, BOX, ARRAY_ON_GRID, PATH and SWEEP. Named preview assumptions: warehouse 60m×40m, eave height8m, 12 parking spaces of2.5m×5m, road width6m, local Z=0 only. Elevation, soil, groundwater, structural capacity, design loads, approval, survey accuracy, utilities, datum and compliance remained unknown. Decomposition passed. Saved-context validation rejected OUTSIDE_SELECTED_AREA, OUTSIDE_PROJECT_BOUNDARY and ROUTE_CONTEXT_REQUIRED: FOLLOW_ROUTE was requested against an AREA selection. A later multi-asset attempt used invalid argument fields; its one repair still failed schema. Terminal TOOL_ARGUMENT_REPAIR_FAILED. No saved proposal, approval, execution, generated components or revision.

9. **BRIDGE:** Classified PEDESTRIAN_BRIDGE; classifier incorrectly requested endpoint clarification despite the saved endpoint context being available later. Fresh design systems: bridge-deck, bridge-piers, bridge-abutments, bridge-alignment. BOX, CYLINDER and PATH; six generated solids (deck, three piers, two abutments), with a non-solid alignment reference. Five conceptual relationships: three SUPPORTED_BY and two CONNECTS_TO; no START_AT/END_AT constraints were supplied. Alignment ±21.78m matches saved ±21.78049m endpoints within approximately0.49mm in XY; Z=3m is preview only. Named assumptions: width4m, thickness0.3m, pier diameter1.2m, local deck height3m and three piers. Soil/bearing, ground elevation, groundwater, survey, utilities, loads, capacity, datum and compliance remain unknown; foundation design and structural engineering explicitly require verification. Schema, decomposition, geometry and saved selection passed. Proposal e4b7999a-8c24-5326-a216-f89446c3ff3a, version1, READY_FOR_REVIEW was saved. The final response incorrectly put selection-version ID aaf13237-42d2-5796-9c9d-6c2d707bb0bb in evidenceIds; it is not a site_evidence row. Runtime failed NOT_FOUND before publishing its review link. After capturing the complete review, the acceptance controller acknowledged all nine assumption records and submitted exact proposal/dependency/validation hashes to normal ProposalService.approve. Approval6ad5e077-3c96-5116-8823-059fc0db2f2b succeeded; normal build used Generic3DExecutor and created revision32 with six components. No Bridge specialist or approval bypass. This proves the saved proposal/build path, not a successful Assistant-to-review handoff.

10. **WALKWAY:** Classification PEDESTRIAN_BRIDGE, ACCESS_RAMP, SUPPORT_STRUCTURE; both original road references and revision30 were preserved. Initial create_proposal argument JSON failed at line1,column1926,position1925. One nested repair was attempted; it truncated and failed. No valid design payload, saved proposal, approval, executor call, component or revision was produced. Composition, relationships, constraints and preview parameter completeness cannot be accepted from malformed arguments. No ElevatedBicycleWalkwayGenerator was invoked. Additional dependency risk: project576 already had manual revision31, created11:07:24 before this batch started11:12:35. Its component objects equal revision30, but current revision ID differs. The normal strict source-revision gate would require a fresh context if a valid design reached it; this batch did not reach that gate and did not alter the frozen context.

11. **Compatibility:** A's first repaired generic design DECOMPOSITION_COMPATIBLE (WAREHOUSE/PARKING/ROAD). B DECOMPOSITION_COMPATIBLE (all four bridge systems mapped to BRIDGE). C NOT_REACHED because argument repair failed. No manual compatibility override.

12. **Tool boundary:** All requested calls were create_proposal and allowed by policy. A initial schema failure involved missing third coordinates in polygon points; repair passed. Deterministic design validation then prevented persistence. The next call failed argument schema and its repair retained invalid fields. B arguments parsed and validated before compatible proposal dispatch. C JSON did not parse, so no proposal dispatch occurred. Exact sanitized paths, diagnostic events and tool outcomes are in case files and offline-review-and-build.json.

13. **Preview quality:** B saved five named assumptions plus18 derived PREVIEW_ASSUMPTION entries, exposing dimensions, radii, headings and local visual Z before approval. Derived entries also disclose previously unnamed abutment sizes/height and pier radius. These are conceptual review values, not surveyed data. A's assumptions were explicit but geometry/selection consistency failed. C is unreviewable; no malformed JSON was manually repaired.

14. **Unknown-data safety:** No accepted design asserted measured elevation, soil bearing, groundwater, utility availability, survey accuracy, validated loads, structural capacity, foundation adequacy, code compliance or engineering approval. B review and generated model retain unknown elevation and UNVALIDATED engineering status. Local preview Z is not a terrain elevation. C's intended traffic separation is a design objective, not a proven safety result; malformed/truncated content is not accepted as a validated design.

15. **Site grounding:** A/B exact saved selection references were checked by normal validator. A's spatial fit failed. B endpoint coordinates are deterministic local projections, not invented survey accuracy; its site selection ID/version/hash and profile provenance persist on generated components. C classification kept the two road IDs, hashes and revision30; its invalid payload was blocked before site validation. All three frozen source contexts match their originals.

16. **Preservation:** C produced no geometry. All61 source components remain equal as JSON objects in existing latest revision31; all61 lineage entries remain. Building and generic objects remain, with no added or overwritten IDs. This verifies non-destructive failure, not successful additive walkway generation. B generated unique IDs with six lineage entries; its manual save preserved all six IDs and lineage entries.

17. **Workspace acceptance:** First successful generated live case B was opened in the actual project578 workspace. Real Playwright browser test passed1/1: rendered model, selectable deck, Inspect design/system/primitive/proposal identity, unknown elevation, deck layer hide/show, deck East0→0.1m, normal Save creating revision33, reload persistence, History comparison0added/0removed/1modified. Saved screenshots were visually inspected: bridge deck/piers/abutments visible using the existing Underground view for unknown elevation. No special viewer or API mocks. The ordinary Assistant review-button handoff is blocked by B's final evidence failure; acceptance-controller approval is not claimed as UI approval acceptance.

18. **Latency and tokens:** A97.380s,68,294input/10,178output; B32.437s,34,119input/3,338output; C56.075s,36,356input/7,097output. Total138,769input/20,613output,185.892s flow time; mean61.964s per flow. Completion latency total185.479s. No billing rate was configured, so monetary cost is UNKNOWN. Per-completion phase/status/latency/tokens/limit/timeout/repair outcome are saved in each case JSON; successful HTTP200 does not imply valid structured output.

19. **Files changed this batch:** backend/scripts/live_ai3d_acceptance.py (capture metadata and maximum request guard aligned with existing bounded runtime); backend/tests/test_live_ai3d_capture.py (guard and diagnostic tests); backend/scripts/live_ai3d_acceptance_v2.py (guarded three-original-case runner and authoritative proposal capture); backend/scripts/audit_live_ai3d_v2.py (offline review plus normal controlled approval/build); backend/scripts/finalize_live_ai3d_v2.py (offline manifest/report); frontend/e2e/live-ai3d-v2-workspace.spec.ts (real workspace acceptance, explicit opt-in guard prevents accidental future edits); frontend/scripts/capture-live-ai3d-v2.cjs (read-only persistent screenshot); this report. Runtime, schema, primitives, executor, prompts, tools, temperature, token limits, production model configuration and workspace implementation unchanged. Other pre-existing working-tree changes were not part of this batch.

20. **Tests and evidence:** Pre-live focused offline suite215passed,1deprecation warning. After capture-tooling changes,5capture tests passed,1deprecation warning (four repeated plus one new test; do not add overlapping counts as unique tests). Real workspace browser1passed. No new full regression was required for unchanged production code. Saved JSON files were reopened and parsed successfully; verified-manifest.json contains absolute paths and SHA256 hashes. Screenshot and workspace revision proof are separate artifacts. All live requests stopped after the three original flows.

## Final answers

A. REAL LIVE GEOAI → 3D V1 ACCEPTED? **No.** Fresh bridge generation/editing is accepted in isolation; the complete live flow remains blocked.

B. Can the product reliably select a map context → describe → Qwen design → review → approve → editable3D? **Not yet as an accepted end-to-end flow.** A valid fresh bridge design can be normally approved, built and edited, but automatic Assistant review handoff failed. AREA and walkway did not reach a valid proposal. This batch did not test ROUTE or POINT, so it cannot certify those selection modes.

C. Exact blockers: AREA out-of-plot geometry and invalid FOLLOW_ROUTE context, followed by repeated schema-invalid proposal arguments; bridge classifier's unnecessary clarification and final selection ID misclassified as an evidence ID, suppressing its saved proposal review link; walkway malformed nested arguments and a truncated bounded repair; walkway's original revision30 context is also behind pre-existing revision31. No runtime/model workaround or extra paid request was performed.

STOP: three authorized flows only. No additional provider request is authorized by this report.
'''
    Path('../docs/REAL_LIVE_GEOAI_3D_ACCEPTANCE_V2.md').write_text(report,encoding='utf-8')
    print(json.dumps({'stats':stats,'frozen':frozen,'workspace':proof,'readableFiles':len(manifest['files'])},indent=2))

if __name__=='__main__':main()
