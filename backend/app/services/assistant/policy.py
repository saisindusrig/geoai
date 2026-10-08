"""Server policy caps effects independently of provider classifications."""
import re
from app.domain.stage1 import CivilIntent
from app.services.assistant.foundation import capability
from app.services.assistant.decomposition import decompose
from app.core.asset_families import asset_definition

ASSETS = {"building":"BUILDING", "road":"ROAD", "bridge":"BRIDGE", "dam":"DAM", "drainage":"DRAINAGE",
    "tunnel":"TUNNEL", "culvert":"CULVERT", "retaining wall":"RETAINING_WALL", "pipeline":"PIPELINE",
    "canal":"CANAL", "foundation":"FOUNDATION", "embankment":"EMBANKMENT", "grading":"SITE_GRADING",
    "utility corridor":"UTILITY_CORRIDOR", "cofferdam":"COFFERDAM"}


def text_of(message):
    return "\n".join(p.get("text", "") for p in message["parts"] if p["kind"] in {"TEXT", "QUESTION"})


def classify(message):
    text=text_of(message).lower().strip()
    if re.search(r"\b(approve|approval|accept (the |this )?proposal)\b",text):kind="PROPOSAL_APPROVAL"
    elif re.search(r"\b(safe|safety|structural analysis|analy[sz]e|capacity)\b",text):kind="ANALYSIS_REQUEST"
    elif re.match(r"(why|explain)\b",text):kind="EXPLANATION_REQUEST"
    elif re.search(r"\b(slope|elevation|terrain|utilities|soil|flood|readiness)\b",text) and ("?" in text or re.match(r"(what|show|is|are|get)",text)):kind="SITE_QUERY"
    elif re.match(r"(move|raise|lower|translate|change|revise|rotate|resize|remove|delete)\b",text):kind="CHANGE_REQUEST"
    elif re.search(r"\b(build|create|design|plan|want|propose)\b",text) and "?" not in text:kind="DESIGN_REQUEST"
    elif "?" in text or re.match(r"(what|where|how|can|could|would|is|are)\b",text):kind="QUESTION"
    else:kind="GENERAL_DISCUSSION"
    assets=decompose(text)
    ambiguous=kind=="CHANGE_REQUEST" and not message["context"]["selection"] and not message["context"].get("proposalVersionId")
    return CivilIntent(kind=kind,domain="CIVIL_INFRASTRUCTURE",assets=assets[:100],needs_clarification=ambiguous,
        clarification_question="Select the saved objects you want to change, then send the request again." if ambiguous else None)


def evaluate(message, proposed_intent=None):
    intent=classify(message)
    # Model classification may enrich asset names but cannot escalate a read-only request.
    attached={r["objectId"] for r in message["context"]["selection"]}
    if proposed_intent is not None and proposed_intent.kind==intent.kind and all(r.object_id in attached for a in proposed_intent.assets for r in a.referenced_objects):
        intent=proposed_intent.model_copy(update={"needs_clarification":intent.needs_clarification or proposed_intent.needs_clarification})
    intent=intent.model_copy(update={"assets":[a.model_copy(update={"asset_family":asset_definition(a.asset_type)["family"]}) for a in intent.assets]})
    effect="APPROVAL_UI_REQUIRED" if intent.kind=="PROPOSAL_APPROVAL" else "PROPOSAL_ONLY" if intent.kind in {"DESIGN_REQUEST","CHANGE_REQUEST"} and not intent.needs_clarification else "READ_ONLY"
    operation={"DESIGN_REQUEST":"PROPOSE","CHANGE_REQUEST":"PROPOSE","ANALYSIS_REQUEST":"ANALYZE","SITE_QUERY":"DISCUSS"}.get(intent.kind,"DISCUSS")
    return {"intent":intent.model_dump(mode="json",by_alias=True),"allowedEffect":effect,"requestedOperation":operation,
        "targetObjects":message["context"]["selection"],"proposalReference":message["context"].get("proposalVersionId"),
        "capabilities":[capability(a.asset_type).model_dump(mode="json",by_alias=True) for a in intent.assets],
        "limitations":["Only conceptual planning is available; no validated structural safety conclusion or geometry execution is available.",
            "Unknown or unavailable evidence does not establish absence. Approval requires the application review control."]}
