"""Shared controlled tool contracts, independent of DB execution."""
from app.domain.assistant_runtime import NoArguments, TerrainArguments, NearbyArguments, ProposalToolArguments, ProposalReference

SCHEMAS={name:NoArguments for name in ("get_site_profile","get_site_readiness","get_active_terrain","get_selected_objects",
    "get_model_revision","get_project_requirements","get_checks","get_constraints")}
SCHEMAS.update(sample_terrain=TerrainArguments,query_nearby_context=NearbyArguments,
    create_proposal=ProposalToolArguments,revise_proposal=ProposalToolArguments,validate_proposal=ProposalReference)

def envelope(status="OK",data=None,evidence=None,limitations=None,code=None,dependencies=None):
    return {"status":status,"data":data,"evidenceIds":evidence or [],"dependencyRefs":dependencies or [],"limitations":limitations or [],"errorCode":code}

def describe_tools():
    return [{"name":name,"argumentsSchema":schema.model_json_schema(by_alias=True)} for name,schema in SCHEMAS.items()]
