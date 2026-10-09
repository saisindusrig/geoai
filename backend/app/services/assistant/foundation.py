"""Capability and command gates; catalogue entries never confer engineering authority."""
from app.domain.stage1 import AssetCapability, Operation, ProposalCommand

SELECTIONS = {
    "BUILDING": ["AREA"], "ROAD": ["ROUTE", "ENDPOINTS"],
    "BRIDGE": ["CROSSING", "ENDPOINTS"], "DAM": ["AREA", "ROUTE"],
    "RETAINING_WALL": ["ROUTE"], "CULVERT": ["CROSSING"],
    "DRAINAGE": ["ROUTE", "AREA", "POINT"], "TUNNEL": ["ROUTE", "ENDPOINTS"],
}


def capability(asset_type: str, registry=None) -> AssetCapability:
    """Only explicit registered operations confer execution capability.

    Unregistered names stay intact. Discussion eligibility remains independent
    of execution; conceptual geometry is not engineering analysis.
    """
    from app.core.asset_families import asset_definition, FAMILIES
    from app.services.assistant.specialists import ADAPTERS
    definition=asset_definition(asset_type)
    adapter=(registry or ADAPTERS).resolve(asset_type)
    operations=set(adapter.metadata.capabilities) if adapter else set()
    return AssetCapability(
        asset_type=asset_type, asset_family=definition["family"],display_name=definition["displayName"],component_kinds=definition["componentKinds"],registry_version="asset-families/1",
        discussion_support="FULL", planning_support="FULL" if "PLAN" in operations else "CONCEPT_ONLY",
        proposal_support="FULL" if "PROPOSE" in operations else "CONCEPT_ONLY", generation_support="FULL" if "GENERATE" in operations else "UNSUPPORTED",
        geometry_validation_support="FULL" if "VALIDATE_GEOMETRY" in operations else "UNSUPPORTED", engineering_analysis_support="FULL" if "ANALYZE" in operations else "UNSUPPORTED",
        site_selection_types=list(FAMILIES[definition["family"]].selection_kinds),
        supported_operations=sorted({"DISCUSS"}|operations),
        patch_capabilities=["BUILDING_PATCH_MOVE_COMPONENT", "BUILDING_PATCH_ROTATE_COMPONENT", "BUILDING_PATCH_OPENING"] if adapter and adapter.metadata.id=="building-concept" else [],
        specification_schema_id=adapter.specification_schema.__name__ if adapter else None,
        generator_id=adapter.metadata.id if adapter and "GENERATE" in operations else None,
        generator_version=adapter.metadata.version if adapter and "GENERATE" in operations else None,
        validator_ids=[adapter.metadata.id] if adapter and "VALIDATE_GEOMETRY" in operations else [],
        analysis_calculator_ids=[adapter.metadata.id] if adapter and "ANALYZE" in operations else [],
        limitations=["Concept discussion and proposals only; no specialist execution adapter is registered."] if not adapter else ["Only this adapter's declared operations are available; conceptual output is not engineering approval.",
            "Building V1: rectangular typed concepts only. No foundations, structural analysis, code compliance, MEP, rebar or BOQ." if adapter.metadata.id=="building-concept" else "Refer to this specialist's typed input schema."],
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
        if isinstance(action, dict) and action.get("type") in {"show_layer", "download", "run_site_analysis"}:
            safe.append(action)
        else:
            rejected.append("PROPOSAL_REQUIRED: assistant actions cannot modify the model; proposal execution is not enabled.")
    return {**result, "actions": safe, "action": safe[0] if len(safe) == 1 else None,
            "warnings": [*(result.get("warnings") or []), *rejected]}
