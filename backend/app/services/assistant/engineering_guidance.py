"""Read-only saved evidence adapter and labeled deterministic offline guidance.

No provider, script runner, proposal mutation or solver invocation is reachable here.
Conversation persistence and execution/authorization remain the existing systems.
"""
import re
import sqlalchemy as sa
from app.services.assistant.storage import owned_row, table, identity, insert, update, digest, lock_project
from app.services.assistant.conversations import reject_secrets
from app.db.models import Project
from app.services.assistant.storage import error
from app.services.assistant.policy import text_of
from app.services.design.opensees_benchmark import digest as engineering_digest

MODELS = ["zai-org/GLM-5.3-Flash", "zai-org/GLM-5.3"]
GROUPS = ["Geometry and section", "Material properties", "Loads", "Supports and connections", "Engineering assumptions", "Analysis and results"]


def group_for(path):
    value = path.lower()
    if any(x in value for x in ("modulus", "material", "strength", "steel", "concrete")): return GROUPS[1]
    if any(x in value for x in ("load", "pressure", "intensity", "force", "moment")): return GROUPS[2]
    if any(x in value for x in ("support", "anchor", "connection", "embedment", "spring")): return GROUPS[3]
    if any(x in value for x in ("geometry", "diameter", "area", "inertia", "section", "size")): return GROUPS[0]
    return GROUPS[4]


def friendly(name):
    return "Platform slab" if name == "platform-deck" else re.sub(r"[-_]", " ", name[:255])


def saved_context(db, project_id, revision_id, selected_ids, dirty=False):
    project = db.get(Project,project_id)
    revision=owned_row(db,"model_revisions",project_id,revision_id) if revision_id else None
    available={c["id"] for c in (revision or {}).get("document_json",{}).get("components",[])}
    if len(selected_ids)>100 or any(i not in available for i in selected_ids):error(422,"UNSAVED_SELECTION","Save new objects or clear the selection before reading saved engineering context.")
    refs=[{"objectId":i} for i in dict.fromkeys(selected_ids)]
    rt = table("model_revisions")
    latest_revision = db.execute(sa.select(rt.c.id).where(rt.c.project_id==project_id).order_by(rt.c.id.desc())).scalar()
    document = revision["document_json"] if revision else None
    document_hash = engineering_digest(document) if document else None
    components = {c["id"]:c for c in (document or {}).get("components",[])}
    selected = []
    for ref in refs:
        c = components[ref["objectId"]]
        cad = c.get("metadata",{}).get("drawing_cad",{})
        selected.append({"id":c["id"],"name":friendly(c["name"]),"role":c.get("category"),"geometry":c["geometry"],
            "transform":c["transform"],"appearance":c.get("material"),"locked":c.get("locked",False),
            "engineeringStatus":c.get("metadata",{}).get("engineering_status","Engineering Unverified"),
            "cadSource":{k:cad[k] for k in ("source_entity_id","source_sha256","component_sha256","input","missing_engineering_inputs") if k in cad}})
    at=table("engineering_analyses")
    records=list(db.execute(sa.select(at).where(at.c.project_id==project_id).order_by(at.c.id.desc()).limit(100)).mappings())
    latest_inputs={}
    for r in records:
        if r["analysis_type"].endswith("_INPUT") and r["model_revision_id"]==revision_id:
            latest_inputs.setdefault(r["analysis_type"],r["id"])
    analyses=[];missing=[];missing_total=0;seen=set()
    for r in records:
        data=r["result_json"] or {};kind=r["analysis_type"]
        stale=bool(dirty or revision_id!=latest_revision or r["model_revision_id"]!=revision_id or r["status"]=="STALE" or
            data.get("model_document_sha256") and data["model_document_sha256"]!=document_hash)
        input_id=data.get("input_record_id")
        if input_id:
            source=next((x for x in records if x["id"]==input_id),None)
            stale=stale or source is None or source["status"]=="STALE" or latest_inputs.get(source["analysis_type"],input_id)!=input_id
        if kind.endswith("_INPUT") and kind not in seen and not stale:
            seen.add(kind)
            values=data.get("assessment",{}).get("missing",data.get("missing",[]))
            missing_total+=len(values)
            for v in values[:1000]:
                path=v.get("path","") if isinstance(v,dict) else str(v)
                missing.append({"group":group_for(path),"path":path,"reason":v.get("reason","") if isinstance(v,dict) else str(v),"recordId":r["id"]})
        if kind not in {"FOUNDATION_SYSTEM_RESULT","OPENSEES_PHYSICAL_FRAME","OPENSEES_SLAB_TRANSFER","REAL_CONNECTION_INPUT","PHYSICAL_FRAME_INPUT","SLAB_TRANSFER_INPUT","AI_ASSEMBLY_PROPOSAL","DRAWING_CAD_SOURCE_REFERENCE"}: continue
        # Frozen, bounded evidence, never whole proposed documents or provider text.
        entry={"id":r["id"],"type":kind,"revisionId":r["model_revision_id"],"status":r["status"],"stale":stale,
            "solverVersion":data.get("solver_version"),"engineeringApproval":data.get("engineering_approval","DISABLED"),
            "inputRecordId":input_id,"limitations":data.get("limitations",[]),"evidenceHash":digest(data)}
        if kind == "FOUNDATION_SYSTEM_RESULT":
            from app.api.routes.foundation_system import history as foundation_history
            try:
                state=foundation_history(project_id,revision_id,db,project.user_id)
                evidence=next((v for v in state['records'] if v['id']==r['id']),None)
                entry['stale']=stale or not evidence or evidence['status']=='STALE'
            except Exception:
                # Unavailable dependencies must never become current evidence.
                entry['stale']=True
            computed=data.get('computed',{})
            entry['foundation']={k:computed.get(k) for k in ('actions','rc','profile','limitations')}
        if kind.endswith("_INPUT"):
            inputs=data.get("inputs",{})
            entry["declaredInputs"]={k:inputs[k] for k in ("sections","supports","support_source","connections","load_pattern","load_n","load_source","load_cases","combination","units","slab_id","beam_ids","intensity_kn_m2","source","support_assumption") if k in inputs}
        if kind.startswith("OPENSEES"):
            frames=data.get("frames",[])
            results=[data] if not frames else [f["result"] for f in frames]
            ids={s["id"] for s in selected}
            member_ids={e["component_id"] for result in results for e in result.get("elements",[])}
            entry["memberIds"]=sorted(member_ids)
            entry["memberNames"]={i:friendly(components[i]["name"]) for i in member_ids if i in components}
            entry["selectionMatch"]=not ids or bool(ids & member_ids) or bool(ids & {data.get("transfer",{}).get("slab_id")})
            entry["cases"]=[]
            for result in results:
                cases=result.get("load_case_results") or [result]
                for case in cases:
                    entry["cases"].append({"name":case.get("case_name","Saved result"),"kind":case.get("case_kind"),"appliedLoads":case.get("applied_loads"),"solverVersion":case.get("solver_version")})
            samples=[{**s,"componentId":e["component_id"]} for result in results for e in result.get("elements",[]) for s in e.get("samples",[]) if not ids or e["component_id"] in ids]
            for key in ("moment_nm","axial_n","shear_n"):
                values=[s for s in samples if isinstance(s.get(key),(int,float))]
                if values:
                    entry[key]={"min":min(s[key] for s in values),"max":max(s[key] for s in values),"unit":"N·m" if key=="moment_nm" else "N"}
            entry["transfer"]={k:v for k,v in data.get("transfer",{}).items() if k in ("area_m2","slab_id","applied_kn","transferred_kn","conservation_error_kn","strips","limitations","idealization","loading")}
            entry["reactionTotalKn"]=data.get("reaction_total_kn")
            entry["reactionBalanceErrorKn"]=data.get("reaction_balance_error_kn")
        analyses.append(entry)
    sources=[]
    for c in components.values():
        cad=c.get("metadata",{}).get("drawing_cad",{})
        if cad.get("source_entity_id"):
            sources.append({"componentId":c["id"],"name":friendly(c["name"]),"sourceEntityId":cad["source_entity_id"],"sourceHash":cad.get("source_sha256"),"geometryHash":cad.get("component_sha256")})
    return {"projectId":project_id,"projectName":project.name,
        "revisionId":revision_id,"revisionNumber":revision.get("revision_number") if revision else None,"latestRevisionId":latest_revision,
        "stale":bool(dirty or revision_id!=latest_revision),"editorDirty":dirty,"documentHash":document_hash,"selected":selected,
        "analysisVersionHash":digest([(r["id"],r["status"]) for r in records]),"drawingReferences":sources[:100],"analyses":analyses[:30],"missing":missing[:1000],"missingTotal":missing_total,"groups":GROUPS,
        "notice":"Saved evidence only. Appearance is not engineering material certification. Numerical verification is not structural approval."}


def answer(question, context):
    q=question.lower(); selected=context["selected"];actions=["inspect","inputs","results"]
    header=f"Project {context['projectId']} · saved revision {context['revisionId']} (v{context['revisionNumber']})."
    if context["stale"]:header+=" STALE context: unsaved edits or a newer revision exist. These are saved values; save/reselect before preparing or authorizing a solve."
    matches=[a for a in context["analyses"] if a["type"].startswith("OPENSEES") and a.get("selectionMatch")]
    current=next((a for a in matches if not a["stale"] and a["status"]=="VERIFIED"),None)
    if re.search(r"script|python|execute code|approve.*(safe|design)|is.*safe|code compliance",q):
        body="This chat cannot execute scripts, approve a design or certify safety. Use the supported engineering forms and exact-hash authorization controls; code compliance and capacity checks remain unsupported where stated."
    elif re.search(r"foundation|footing|punching|reinforcement|bearing|settlement",q):
        result=next((a for a in context['analyses'] if a['type']=='FOUNDATION_SYSTEM_RESULT' and not a['stale']),None)
        if not result:
            body="No current reviewed integrated foundation result is available. Open Analysis → Integrated foundation workflow. Create a separate study from project 804, review the saved column-patch source, and supply independently sourced factored actions, cylinder/cube strengths, steel, soil stiffness/strength, cover and both bar layers. Preview and explicitly authorize the exact calculation. Missing physical connection, geotechnical settlement and disabled edition checks remain blockers."
        else:
            f=result['foundation'];rc=f.get('rc') or {};actions_saved=f.get('actions') or {}
            body=f"Saved foundation evidence #{result['id']} · {result['status']}. Service column {actions_saved.get('service_column_kn')} kN; service gross soil action {actions_saved.get('service_gross_soil_kn')} kN; independently declared factored column {actions_saved.get('factored_column_kn')} kN. No automatic load factors.\n"
            for layer in rc.get('layers',[]):
                body+=f"{layer['direction']}: As {layer['steel_area_mm2']:.3f} mm², d {layer['effective_depth_mm']:.3f} mm, spacing {layer['spacing_mm']:.3f} mm; flexure {layer.get('flexure',{}).get('status')}; one-way shear {layer.get('one_way',{}).get('status')}; development {layer.get('development',{}).get('status')}.\n"
            body+=f"Punching: {rc.get('punching',{}).get('status')}. Compare supported larger square widths, increased thickness and revised orthogonal bar counts using Compare alternatives in the foundation panel. Increased width reduces soil pressure but also changes cantilever projection; recalculate bending and shear. Increased thickness changes depth and self-weight. These are review proposals only; chat cannot apply or authorize changes.\nWinkler displacement is not site settlement approval. Disabled checks, physical load transfer and incomplete detailing prevent a whole-foundation conclusion."
    elif "thickness" in q or re.search(r"change|edit|proposal|prepare|run|authorize",q):
        body="Geometry changes require Inspect → edit dimensions → Preview → Apply → Save model. Saved analyses must then be reviewed for staleness. For numerical work: identify missing inputs → prepare the existing restricted proposal → review its exact evidence/hash → explicitly authorize → run the supported solver in Analysis. Chat does not change geometry, supply missing engineering values, authorize or run a solver."
    elif "missing" in q or "blocked" in q or re.search(r"\bconnection\b",q):
        if context["missing"]:
            groups={g:sum(v["group"]==g for v in context["missing"]) for g in GROUPS}
            complete=context.get("missingTotal",len(context["missing"]))<=len(context["missing"])
            list_notice="Open Missing inputs for the complete saved list." if complete else f"Showing the first {len(context['missing'])} of {context['missingTotal']} missing inputs; open the saved assessment in Analysis for the full list."
            body="Saved assessment identifies missing required information: "+"; ".join(f"{g}: {n}" for g,n in groups.items() if n)+".\n"+"\n".join(f"• {v['path']}: {v['reason']}" for v in context["missing"][:6])+"\n"+list_notice+" Do not infer values from appearance."
        else:body="No missing-value assessment was found for this saved context. That does not mean inputs are complete or that analysis is authorized. Review Geometry/section, Materials, Loads, Supports/connections and Assumptions in the existing forms."
    elif "load" in q:
        if not current:body="No current verified saved analysis matches the selection. Older or stale results are evidence only; select a saved analyzed member and open Results."
        else:
            body=f"Saved analysis {current['id']} · VERIFIED numerical evidence only. Analytical axes: +X East, +Y Up.\n"
            for case in current.get("cases",[])[:8]:
                loads=case.get("appliedLoads") or {}
                body+=f"Case {case['name']}: {loads.get('source','See saved load evidence')}.\n"
                for node,value in loads.get("nodal_loads_si",{}).items():body+=f"  Node {node}: [Fx, Fy, M] = {[v/1000 for v in value]} [kN, kN, kN·m].\n"
                for member,value in loads.get("uniform_global_by_component_n_per_m",{}).items():
                    if any(value):body+=f"  {current.get('memberNames',{}).get(member,member)}: uniform load {[v/1000 for v in value]} kN/m.\n"
            t=current.get("transfer",{})
            if t:
                pressure=t.get('loading',{}).get('intensity_kn_m2')
                if pressure is not None:body+=f"Declared slab pressure {pressure} kN/m².\n"
                reaction=current.get('reactionTotalKn')
                reaction_text=f"{reaction:.6f}" if isinstance(reaction,(int,float)) else "not recorded"
                body+=f"Slab area {t.get('area_m2')} m²; applied {t.get('applied_kn')} kN; transferred {t.get('transferred_kn')} kN; computed reactions {reaction_text} kN (full precision in Technical evidence). One-way tributary allocation, not slab plate/shell FEA.\n"
            body+="Expand Technical evidence for case values, declared self-weight sources and exclusions."
    elif "moment" in q or "result" in q:
        if not current:body="No current verified saved result matches this selection. Select an analyzed member and inspect Results; stale diagrams must not be treated as current calculations."
        else:
            moment=current.get("moment_nm")
            body=f"Saved analysis {current['id']} · VERIFIED · OpenSees {current.get('solverVersion') or next((c['solverVersion'] for c in current.get('cases',[]) if c.get('solverVersion')),'version not recorded')}."
            if moment:body+=f"\nStored bending-moment samples: min {moment['min']/1000:.6f}, max {moment['max']/1000:.6f} kN·m."
            body+="\nOpen Bending moment to display the existing saved diagram. Display scaling is visual; no new solve or safety approval."
            actions=["moment","results","inputs"]
    elif "drawing" in q or "cad" in q or "source" in q:
        body=f"{len(context['drawingReferences'])} CAD-generated components have saved source identities. Source outlines and generated components are distinct. Expand Technical evidence for entity IDs, drawing hashes and geometry hashes; source identity does not verify structural sections or material grades."
        actions=["drawing","inspect","inputs"]
    elif selected:
        c=selected[0];g=c["geometry"];size=g.get("size")
        body=f"{c['name']} · {c['role']}.\n"+(f"Geometry dimensions {size} m (local size before scale); scale {c['transform']['scale']}.\n" if size else f"Geometry type {g['kind']}; inspect its saved definition.\n")
        body+=f"Position East/North/Up {c['transform']['position']} m; rotation X/Y/Z {c['transform']['rotation_deg']} degrees.\nAppearance: {(c.get('appearance') or {}).get('name','not recorded')}. Engineering status: {c['engineeringStatus']}."
        section=next((s for a in context['analyses'] if not a['stale'] for s in a.get('declaredInputs',{}).get('sections',[]) if s.get('component_id')==c['id']),None)
        if section:body+=f"\nSaved declared section: E {section.get('elastic_modulus_pa')} Pa; A {section.get('area_m2')} m²; I {section.get('inertia_m4')} m⁴. Material {section.get('material_name')}; source: {section.get('material_source')}. Declaration is not material certification."
        else:body+="\nNo matching declared E/A/I was found in the current saved frame input records. Supply explicit section/material evidence; appearance cannot establish those values."
        body+=" Strength, connection capacity and design approval are not established by this explanation."
    else:body="Select a structural component to inspect its saved geometry and source. You can ask about missing inputs, applied loads, saved results or CAD identity. Existing Analysis forms provide proposals and authorization; this offline guidance makes no model-reasoning claim."
    return header+"\n\n"+body+"\n\nEngineering approval remains disabled; supported numerical evidence never certifies the whole structure.",actions


def complete_offline(db,p,run,message):
    from app.services.assistant.runtime import event
    context=saved_context(db,p,int(message["context"]["modelRevisionId"]) if message["context"].get("modelRevisionId") else None,
        [s["objectId"] for s in message["context"]["selection"]],message["context"].get("editorDirty",False))
    text,actions=answer(text_of(message),context)
    snapshot={"mode":"ENGINEERING_OFFLINE","requestedModel":run["context_snapshot"].get("requestedModel",MODELS[0]),"actualModel":None,
        "producer":"Deterministic offline fixture · saved evidence adapter","evidence":context,"actions":actions}
    reject_secrets(text)
    lock_project(db,p)
    convo=owned_row(db,"project_conversations",p,run["conversation_id"])
    insert(db,"conversation_messages",id=identity(run["id"],"reply"),project_id=p,conversation_id=convo["id"],sequence=convo["next_sequence"],role="ASSISTANT",
        parts=[{"kind":"TEXT","text":text[:6000]}],context=message["context"],client_request_id=None)
    update(db,"project_conversations",p,convo["id"],next_sequence=convo["next_sequence"]+1)
    update(db,"assistant_runs",p,run["id"],status="COMPLETE",error_code=None,context_snapshot={**run["context_snapshot"],"engineeringGuidance":snapshot})
    event(db,p,run["id"],"COMPLETE","Saved evidence response complete · offline, no inference")
    db.commit()
