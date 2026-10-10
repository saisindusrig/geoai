"""Projection semantics and strict original schemas; no provider calls."""
from copy import deepcopy
import json
import pytest
from app.experimental.bim_authoring import stage_packet,stage_context,compact_schema,capabilities,MANDATORY_UNKNOWNS
from app.experimental.bim_authoring_fixtures import authoring_case
from app.experimental.cad_contract import digest
from app.domain.bim_authoring import AuthoringIntent,AssemblyPlan,AssemblyExpansion,AssemblyRelationships


def snapshot():
    return dict(userRequest="Design an elevated industrial maintenance platform with columns, primary and secondary steel beams, and a platform slab. Organize the structure into three BIM assemblies. Use explicit metre dimensions, supported sections and materials. Include component identities, placement, dependency relationships, support intent and clearance unknowns. This is a preliminary concept, not a structural engineering design.",
        selectionVersionId="owned-selection",selectionKind="AREA",objectIds=["owned-object"],evidenceIds=["owned-evidence"],
        explicitUnknowns=list(MANDATORY_UNKNOWNS),acceptedRequirements=[{"content":{"key":"user.preference","value":"steel"}}],
        source={"projectId":490001},siteSelection={"largeGeometry":"retained on server"},capabilities=capabilities(),
        siteProfile={"dimensions":{"area":{"status":"KNOWN","value":123}},"verticalReference":{"status":"UNKNOWN"},
            "terrain":{"sampleSummary":{"valid":0}},"unusedLarge":"retained on server"})


@pytest.mark.parametrize("stage",["UNDERSTAND","PLAN","EXPAND","RELATE"])
def test_projections_retain_binding_unknowns_and_requirements(stage):
    frozen=snapshot();original=deepcopy(frozen)
    projected=stage_context(stage,frozen,digest(frozen))
    assert frozen==original
    assert projected["frozenContextHash"]==digest(frozen)
    for key in ("selectionVersionId","selectionKind","objectIds","evidenceIds","acceptedRequirements","explicitUnknowns"):
        assert projected[key]==frozen[key]
    assert not set(projected)&{"source","siteProfile","siteSelection","capabilities","userRequest"}
    if stage != "UNDERSTAND":assert projected["userRequirementsText"]==frozen["userRequest"]
    if stage in {"UNDERSTAND","PLAN"}:assert projected["siteSummary"]["verticalReference"]["status"]=="UNKNOWN"
    projected["objectIds"].append("untrusted-mutated-input")
    projected["acceptedRequirements"][0]["content"]["value"]="changed"
    assert frozen==original


def test_light_understand_original_schema_minimal_output():
    frozen=snapshot()
    packet=stage_packet("UNDERSTAND",request_text=frozen["userRequest"])
    assert "recipes" not in packet["capabilities"]
    assert packet["outputSchema"]==compact_schema(AuthoringIntent.model_json_schema(by_alias=True))
    minimal=dict(requestedStructure=frozen["userRequest"],systems=[dict(id="platform",assetType="INDUSTRIAL_PLATFORM",
        purpose="Industrial maintenance platform; steel preference; no user dimensions supplied",compatibleSelectionKinds=["AREA"])])
    parsed=AuthoringIntent.model_validate(minimal)
    assert len(parsed.systems)==1 and not parsed.requested_features
    assert len(json.dumps(parsed.model_dump(mode="json",by_alias=True)))<1500


@pytest.mark.parametrize("stage,contract",[("UNDERSTAND",AuthoringIntent),("PLAN",AssemblyPlan),("EXPAND",AssemblyExpansion),("RELATE",AssemblyRelationships)])
def test_schema_validation_keywords_unchanged(stage,contract):
    original=contract.model_json_schema(by_alias=True)
    compact=compact_schema(original)
    assert compact["additionalProperties"] is False
    def paths(v,p=()):
        if isinstance(v,dict):
            for k,x in v.items():
                if k!="title":yield from paths(x,(*p,k))
        elif isinstance(v,list):
            for i,x in enumerate(v):yield from paths(x,(*p,i))
        else:yield p,v
    assert dict(paths(original))==dict(paths(compact))


def test_downstream_receives_full_relevant_recipe_keys_and_refs():
    bundle=authoring_case("platform")
    plan_packet=stage_packet("PLAN",intent=bundle.intent)
    assert plan_packet["capabilities"]["sectionParameters"]["I"]==["width","depth","web","flange"]
    for a in bundle.plan.assemblies:
        packet=stage_packet("EXPAND",intent=bundle.intent,plan=bundle.plan,assembly_id=a.id)
        assert packet["input"]["materials"] and packet["input"]["crossSections"]
        assert packet["input"]["planHash"]==digest(bundle.plan)
        for e in bundle.expansions:
            if e.assembly_id==a.id:
                assert all(c.recipe.operation in packet["capabilities"]["recipes"] for c in e.components)
    relate=stage_packet("RELATE",intent=bundle.intent,plan=bundle.plan,expansions=bundle.expansions)
    assert {c["id"] for c in relate["input"]["components"]}=={c.id for e in bundle.expansions for c in e.components}
    assert "materials" not in relate["input"] and "crossSections" not in relate["input"]
