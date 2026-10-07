"""Capability and command gates; no providers, geometry writers or jobs."""
from app.domain.stage1 import AssetCapability, Operation, ProposalCommand

SELECTIONS = {
    "BUILDING": ["AREA"], "ROAD": ["ROUTE", "ENDPOINTS"],
    "BRIDGE": ["CROSSING", "ENDPOINTS"], "DAM": ["AREA", "ROUTE"],
    "RETAINING_WALL": ["ROUTE"], "CULVERT": ["CROSSING"],
    "DRAINAGE": ["ROUTE", "AREA", "POINT"], "TUNNEL": ["ROUTE", "ENDPOINTS"],
}


def capability(asset_type: str) -> AssetCapability:
    """Foundation capabilities, NOT the later vertical-slice release claims.

    Unregistered names stay intact. Discussion eligibility is independent of
    execution. All Stage 1 proposal/generation adapters remain unimplemented.
    """
    return AssetCapability(
        asset_type=asset_type, registry_version="foundation/1",
        discussion_support="FULL", planning_support="CONCEPT_ONLY",
        proposal_support="CONCEPT_ONLY", generation_support="UNSUPPORTED",
        geometry_validation_support="UNSUPPORTED", engineering_analysis_support="UNSUPPORTED",
        site_selection_types=SELECTIONS.get(asset_type.upper(), []),
        supported_operations=["DISCUSS"],
        limitations=["Concept discussion only. Stage 1 execution adapters are not enabled."],
    )


def require_execution(asset_type: str, operation: Operation) -> AssetCapability:
    result = capability(asset_type)
    if operation not in result.supported_operations:
        raise ValueError(f"UNSUPPORTED_OPERATION: {operation} for {asset_type}")
    return result


def submit_proposal_command(command: ProposalCommand) -> None:
    """Future application-service seam, deliberately fail-closed today."""
    raise NotImplementedError("PROPOSAL_SERVICE_UNAVAILABLE: no geometry was changed")


def guard_assistant_response(result: dict) -> dict:
    """Strip legacy executable commands even when the provider misbehaves."""
    actions = result.get("actions") or ([result["action"]] if result.get("action") else [])
    safe, rejected = [], []
    for action in actions:
        if isinstance(action, dict) and action.get("type") in {"show_layer", "download"}:
            safe.append(action)
        else:
            rejected.append("PROPOSAL_REQUIRED: assistant actions cannot modify the model; proposal execution is not enabled.")
    return {**result, "actions": safe, "action": safe[0] if len(safe) == 1 else None,
            "warnings": [*(result.get("warnings") or []), *rejected]}
