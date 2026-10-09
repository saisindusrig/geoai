"""Deterministic request grounding layered on the existing policy and catalogue."""
import re
from app.core.asset_families import asset_definition

UNKNOWN_FIELDS=("elevation", "soilBearingCapacity", "groundwater", "surveyAccuracy",
                "utilityLocations", "structuralCapacity", "designLoads", "verticalDatum", "codeCompliance")


def translation_from_request(text, selection, revision):
    match=re.search(r"\b(?:move|translate)\b.*?\b(\d+(?:\.\d+)?)\s*(mm|m|metres?|meters?)\s+(east|west|north|south|up|down)\b",text.lower())
    if not match or not selection or not revision:return None
    distance=float(match[1])/(1000 if match[2]=="mm" else 1)
    # Saved editable documents use ENU (frontend/lib/editor-transform.ts).
    vectors={"east":(1,0,0),"west":(-1,0,0),"north":(0,1,0),"south":(0,-1,0),"up":(0,0,1),"down":(0,0,-1)}
    return {"objectIds":[r["objectId"] for r in selection],"coordinateSystem":"LOCAL",
            "deltaM":[distance*v for v in vectors[match[3]]],"sourceModelRevisionId":revision,
            "derivation":{"inputDistance":match[1],"inputUnit":match[2],"direction":match[3],"distanceM":distance}}


def understand(message, policy):
    from app.services.assistant.policy import text_of
    text=text_of(message);lower=text.lower();context=message["context"]
    assets=policy["intent"]["assets"];kind=policy["intent"]["kind"]
    edges=[]
    def link(a,b,relation):
        edge={"fromAssetRequestId":a["id"],"toAssetRequestId":b["id"],"kind":relation}
        if a["id"]!=b["id"] and edge not in edges:edges.append(edge)
    buildings=[a for a in assets if a["assetFamily"]=="BUILDING"]
    for a in assets:
        if a["assetFamily"]=="ROAD":
            for b in buildings:link(b,a,"CONNECTS_TO")
        if a["assetFamily"]=="WATER":
            for b in buildings:link(a,b,"SERVES")
        if a["assetFamily"]=="DRAINAGE":
            for b in assets:
                if b["assetFamily"] in {"SITE","BUILDING"}:link(b,a,"DRAINS_TO")
        if a["assetFamily"]=="BRIDGE" and re.search(r"\b(connect|connecting|connected)\b",lower):
            for b in buildings:link(b,a,"CONNECTS_TO")
    tools=[]
    def need(*names):
        for name in names:
            if name not in tools:tools.append(name)
    if kind=="CHANGE_REQUEST" and context["selection"]:need("get_selected_objects","get_model_revision")
    if re.search(r"\b(selected|selection)\b",lower) or re.search(r"what (?:do i|objects do i) have selected",lower):need("get_selected_objects")
    if kind=="SITE_QUERY" or (kind=="EXPLANATION_REQUEST" and re.search(r"\b(site|ready|readiness)\b",lower)):need("get_site_readiness","get_site_profile")
    if re.search(r"\b(check|checks|failed)\b",lower) and kind=="EXPLANATION_REQUEST":need("get_checks","get_model_revision")
    if kind=="DESIGN_REQUEST":
        need("get_site_profile","get_site_readiness")
        if re.search(r"\b(steep|slope|terrain|drainage|drain)\b",lower):need("get_active_terrain","sample_terrain")
        need("revise_proposal" if context.get("proposalVersionId") else "create_proposal","validate_proposal")
    if kind=="CHANGE_REQUEST" and not policy["intent"]["needsClarification"]:need("revise_proposal" if context.get("proposalVersionId") else "create_proposal","validate_proposal")
    translation=translation_from_request(text,context["selection"],context.get("modelRevisionId"))
    return {"schemaVersion":"request-understanding/1","objective":text,"intent":kind,"assets":assets,
        "relationships":edges,"referencedObjects":context["selection"],"siteDependency":kind in {"DESIGN_REQUEST","SITE_QUERY","ANALYSIS_REQUEST"},
        "operation":policy["requestedOperation"],"capabilityRequirements":policy["capabilities"],
        "catalogueCandidates":[asset_definition(a["assetType"]) for a in assets][:20],
        "requiredTools":tools,"sourceModelRevisionId":context.get("modelRevisionId"),
        "siteSelectionVersionId":context.get("siteSelectionVersionId"),"siteProfileVersionId":context.get("siteProfileVersionId"),
        "axisConvention":{"coordinateSystem":"LOCAL","x":"east","y":"north","z":"up","source":"saved editable document ENU convention"},
        "proposedTranslation":translation,"unknowns":{field:"UNKNOWN" for field in UNKNOWN_FIELDS},
        "assumptions":[],"expectedEffect":policy["allowedEffect"],"approvalRequired":policy["allowedEffect"]=="PROPOSAL_ONLY"}
