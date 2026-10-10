"""Typed, project-owned references and deterministic evidence resolution."""
from app.services.assistant.storage import owned_row, rows
from app.services.ai.provider import AssistantProviderError

def references(db,p,context):
    result={'selectionReference':None,'siteProfileReference':None,'modelRevisionReference':None,'evidenceReference':[]}
    for key,field,table,kind,alias in [('selectionReference','siteSelectionVersionId','site_selection_versions','SELECTION_VERSION','selected-area'),
        ('siteProfileReference','siteProfileVersionId','site_profile_versions','SITE_PROFILE_VERSION','terrain-profile'),
        ('modelRevisionReference','modelRevisionId','model_revisions','MODEL_REVISION','current-model')]:
        if context.get(field):
            row=owned_row(db,table,p,context[field])
            result[key]={'kind':kind,'id':str(row['id']),'alias':alias}
    if context.get('siteProfileVersionId'):
        ids=sorted({r['evidence_id'] for r in rows(db,'site_profile_evidence',p) if r['profile_version_id']==context['siteProfileVersionId']})[:8]
        result['evidenceReference']=[{'kind':'EVIDENCE','id':owned_row(db,'site_evidence',p,eid)['id'],'alias':f'site-evidence-{i+1}'} for i,eid in enumerate(ids)]
    return result

def resolve_evidence(db,p,context,requested,outputs,diagnostics):
    refs=references(db,p,context)
    allowed={r['id'] for r in refs['evidenceReference']}
    aliases={r['alias']:r['id'] for r in refs['evidenceReference']}
    for output in outputs:
        for eid in output.get('result',{}).get('evidenceIds',[]):
            owned_row(db,'site_evidence',p,eid);allowed.add(eid)
    non_evidence={r['id'] for k,r in refs.items() if k!='evidenceReference' and r}
    for value in requested:
        if value in allowed or value in aliases:continue
        if value in non_evidence or value in {'selected-area','current-model','terrain-profile'}:
            diagnostics.append({'event':'REFERENCE_TYPE_MISMATCH','expectedKind':'EVIDENCE','resolution':'SERVER_DERIVED_EVIDENCE_ONLY'})
            continue
        # Arbitrary and other-project IDs remain forbidden. Never silently accept them.
        raise AssistantProviderError('EVIDENCE_REFERENCE_INVALID')
    # The model's opaque references never become authority. Only frozen/profile and tool-owned evidence is stamped.
    return sorted(allowed)[:20]
