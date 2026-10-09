"""Exactly three live PRIMARY flows. Checkpoint each request; never approve here."""
import asyncio
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from pydantic import ValidationError
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import User, Project, DesignScenario, ModelRevision
from app.domain.site_workspace import SelectionInput, ConversationInput, MessageInput
from app.domain.stage1 import CivilIntent
from app.domain.assistant_runtime import ProviderResponse
from app.services.site_profiles.selection import save_selection
from app.services.site_profiles.service import SiteProfileService
from app.services.assistant.conversations import ConversationService
from app.services.assistant.runtime import queue_run, process
from app.services.assistant.storage import owned_row, rows
from app.services.ai.provider import NebiusProvider
from app.services.ai.response_metadata import validation_metadata
from test_site_workspace import AREA, WGS84

OUT = Path("live-results/universal-v1")
MODEL = "Qwen/Qwen3.5-397B-A17B"

def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    temporary.replace(path)

def safe(value):
    if isinstance(value, dict):
        return {k:safe(v) for k,v in value.items() if k not in {"reasoning", "reasoning_content", "chain_of_thought"}}
    if isinstance(value, list): return [safe(v) for v in value]
    if isinstance(value, str):
        for key, secret in settings.model_dump().items():
            if any(s in key for s in ("KEY", "TOKEN", "SECRET", "DATABASE_URL", "REDIS_URL")) and isinstance(secret,str) and len(secret)>=6:
                value=value.replace(secret,"[REDACTED]")
    return value

class CapturedProvider(NebiusProvider):
    def __init__(self, result, path):
        self.result, self.path = result, path
        super().__init__(usage_sink={})
    async def complete(self, system, payload, route):
        if route.model!=MODEL or route.tier!="PRIMARY": raise RuntimeError("MODEL_GUARD")
        if len(self.result["completions"])>=20: raise RuntimeError("REQUEST_BUDGET")
        entry={"requestNumber":len(self.result["completions"])+1,"model":route.model,
            "schema":payload["schema"].get("title"),"repairAttempt":bool(payload.get("repair")),
            "maxOutputTokens":route.max_output_tokens,"status":"STARTED"}
        self.result["completions"].append(entry)
        save(self.path,self.result)
        start=time.monotonic(); before=len(self.metadata_sink); previous=dict(self.usage_sink)
        try:
            value=await super().complete(system,payload,route)
            schema=CivilIntent if entry["schema"]=="CivilIntent" else ProviderResponse
            try:
                parsed=schema.model_validate(value)
                entry.update(structuredValid=True,visibleStructuredResponse=safe(parsed.model_dump(mode="json",by_alias=True)))
            except ValidationError as exc:
                entry.update(structuredValid=False,**validation_metadata(exc,payload["schema"]))
            entry["status"]="RETURNED"
            return value
        except Exception as exc:
            entry.update(status="FAILED",errorCode=getattr(exc,"code",type(exc).__name__),structuredValid=False)
            entry["providerDiagnostics"]=safe(getattr(exc,"diagnostics",{}))
            raise
        finally:
            entry["latencySeconds"]=round(time.monotonic()-start,3)
            entry["providerMetadata"]=safe(self.metadata_sink[before:])
            entry["inputTokens"]=(self.usage_sink["prompt_tokens"]-previous.get("prompt_tokens",0)) if self.usage_sink.get("prompt_tokens") is not None else None
            entry["outputTokens"]=(self.usage_sink["completion_tokens"]-previous.get("completion_tokens",0)) if self.usage_sink.get("completion_tokens") is not None else None
            save(self.path,self.result)

async def main():
    if (settings.NEBIUS_PRIMARY_MODEL.strip() or settings.NEBIUS_CHAT_MODEL)!=MODEL or settings.NEBIUS_FAST_MODEL.strip():
        raise RuntimeError("CONFIGURATION_GUARD")
    OUT.mkdir(parents=True,exist_ok=False)  # A used batch cannot be accidentally rerun.
    cases=[("A","AREA","Create a small warehouse with parking and an access road here."),
        ("B","ENDPOINTS","Create a pedestrian bridge between these points."),
        ("C","AREA","Create an elevated bicycle walkway over the road.")]
    for case,kind,prompt in cases:
        path=OUT/f"case-{case}.json"
        result={"case":case,"selectionType":kind,"userRequest":prompt,"model":MODEL,"completions":[],"approval":"NOT_APPROVED"}
        save(path,result)
        with SessionLocal() as db:
            user=db.query(User).order_by(User.id).first()
            base=None
            if case=="C":
                project=db.get(Project,576)
                if not project or project.user_id!=user.id: raise RuntimeError("FIXTURE_OWNERSHIP")
                base=db.query(ModelRevision).filter_by(project_id=project.id).order_by(ModelRevision.id.desc()).first()
                scenario=db.get(DesignScenario,base.design_scenario_id)
            else:
                project=Project(user_id=user.id,name=f"Live GeoAI 3D acceptance {case}",project_type="building",center_lng=77.001,center_lat=12.0005,boundary_geojson=AREA)
                db.add(project);db.flush()
                scenario=DesignScenario(project_id=project.id,name=f"Live {case}",status="draft")
                db.add(scenario);db.commit()
            selection={"kind":"AREA","geometry":AREA} if kind=="AREA" else {"kind":"ENDPOINTS","endpointA":{"type":"Point","coordinates":[77.001,12.0005]},"endpointB":{"type":"Point","coordinates":[77.0014,12.0005]}}
            selected=save_selection(db,project.id,user.id,SelectionInput(selection=selection,original_crs=WGS84))
            profiles=SiteProfileService();prepared,_=profiles.prepare(db,project.id,user.id,selected["id"])
            profiles.build(db,project.id,prepared["id"],prepared["jobId"])
            profile=profiles.read(db,project.id,prepared["id"])["version"]
            convo=ConversationService().create(db,project.id,user.id,ConversationInput(client_request_id=f"live-{case}"))
            context={"siteSelectionVersionId":selected["id"],"siteProfileVersionId":profile["id"],"scenarioId":str(scenario.id)}
            if base:
                context.update(modelRevisionId=str(base.id),selectedObjectIds=[c["id"] for c in base.document_json["components"] if c.get("metadata",{}).get("systemAssetType")=="ROAD"][:2])
            posted=ConversationService().submit(db,project.id,user.id,convo["id"],MessageInput(client_request_id=f"live-{case}",parts=[{"kind":"TEXT","text":prompt}],context=context))
            result.update(projectId=project.id,scenarioId=scenario.id,conversationId=convo["id"],runId=posted["runId"],messageId=posted["messageId"],sourceRevisionId=str(base.id) if base else None)
            save(path,result)
            queue_run(db,project.id,user.id,posted["runId"])
            started=time.monotonic()
            await process(db,project.id,posted["runId"],CapturedProvider(result,path))
            run=owned_row(db,"assistant_runs",project.id,posted["runId"])
            result.update(runStatus=run["status"],errorCode=run["error_code"],latencySeconds=round(time.monotonic()-started,3),runContext=safe(run["context_snapshot"]))
            messages=[m for m in rows(db,"conversation_messages",project.id) if m["conversation_id"]==convo["id"]]
            result["visibleMessages"]=safe([{k:m[k] for k in ("id","role","parts")} for m in messages])
            vids=[p["proposalVersionId"] for m in messages for p in m["parts"] if p["kind"]=="PROPOSAL"]
            from app.services.assistant.proposals import ProposalService
            result["proposals"]=safe([ProposalService().read(db,project.id,v) for v in vids])
            save(path,result)
            print(json.dumps({"case":case,"status":run["status"],"errorCode":run["error_code"],"requests":len(result["completions"]),"path":str(path)}),flush=True)
    print("STOP: all three authorized flows attempted; no approval or build performed automatically.",flush=True)

if __name__=="__main__": asyncio.run(main())
