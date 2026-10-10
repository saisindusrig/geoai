"""Local, opt-in intent adapter. No inference, approvals or geometry writes."""
import json
import re

from shapely.geometry import shape
from app.core.config import settings
from app.services.assistant.policy import evaluate, text_of
from app.services.assistant.platform_template import platform_design

LABEL = "Offline demo · supported platform template"
EXAMPLE = "Create a 5 m × 3 m industrial maintenance platform with columns, beams and a slab. Deck top around 3 m high."
# Full matching prevents silently dropping extra requirements (stairs, loading, etc.).
SUPPORTED = re.compile(
    r"(?:create|design|propose) (?:a |an )?5(?:\.0)?\s*m\s*[x×]\s*3(?:\.0)?\s*m "
    r"industrial maintenance platform(?: concept)? with columns,? beams and (?:a )?slab"
    r"(?:\.\s*deck top (?:around |approximately |at )?3(?:\.0)?\s*m high)?\.?", re.I)


def enabled():
    return (settings.GEOAI_OFFLINE_PLATFORM_DEMO and settings.AI_PROVIDER == "mock"
            and settings.ENVIRONMENT.lower() == "development")


def provider_for_request(db, project_id, message):
    text = " ".join(text_of(message).split())
    if not enabled() or not re.match(r"(?:create|design|propose)\b", text, re.I) or not re.search(r"\bplatform\b", text, re.I):
        return None
    return OfflinePlatformProvider(db, project_id, message, bool(SUPPORTED.fullmatch(text)))


class OfflinePlatformProvider:
    disable_proposal_fallback = True
    def __init__(self, db, project_id, message, supported):
        self.db, self.project_id, self.message = db, project_id, message
        self.supported = supported
        self.turn = 0

    async def complete(self, system, payload, route):
        self.turn += 1
        if self.turn == 1:
            return evaluate(self.message)["intent"]
        if not self.supported:
            return {"text": f"{LABEL}. This demo supports only the 5 m × 3 m platform with four columns, four beams and one slab at local deck top 3 m. Other dimensions or features require a separate supported workflow. Use: {EXAMPLE}"}
        if self.turn == 2:
            from app.services.assistant.ai3d_validation import site_summary
            from app.services.assistant.storage import error
            if not self.message["context"].get("siteProfileVersionId"):
                error(409, "SITE_PROFILE_REQUIRED", "Save the site boundary and Refresh site before requesting this offline platform.")
            summary = site_summary(self.db, self.project_id, self.message["context"])
            # Keep the existing saved model's frame, including nonzero site offsets.
            center = shape(summary["localGeometry"]).centroid
            design = platform_design(summary["selectionReference"], summary["sourceModelRevisionId"], (center.x, center.y))
            # A fixed template must never enter the model-driven design repair path.
            from app.services.assistant.design_flow import validation_errors
            issues = validation_errors(self.db, self.project_id, self.message["context"], design)
            if issues:
                from app.services.ai.provider import AssistantProviderError
                raise AssistantProviderError("OFFLINE_PLATFORM_SITE_UNSUPPORTED", {"issueCodes": sorted({i["code"] for i in issues})})
            arguments = {
                "title": "5 m × 3 m industrial maintenance platform",
                "rationale": f"{LABEL}. Nine conceptual components; local deck top approximately 3 m. No LLM was called.",
                "warnings": ["Loads, foundations, clearances, structural adequacy and code compliance are unverified."],
                "assets": [{"assetType": "AI3D_DESIGN", "name": "Maintenance platform", "ai3dDesign": design}],
            }
            return {"toolCalls": [{"name": "create_proposal", "arguments": json.dumps(arguments)}]}
        results = payload.get("toolResults", [])
        if results and results[-1]["result"]["status"] != "OK":
            from app.services.ai.provider import AssistantProviderError
            raise AssistantProviderError(results[-1]["result"].get("errorCode") or "PROPOSAL_FAILED")
        return {"text": f"{LABEL}. Review the saved proposal, assumptions and validation results. Explicit approval is required before Generate 3D. This is a conceptual visualization, not an engineered structure."}
