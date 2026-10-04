"""Guardrails applied to every AI design output after schema validation."""

MANDATORY_RISKS = [
    "Soil bearing capacity not verified by geotechnical investigation",
    "Existing underground utilities not verified",
    "Land ownership / acquisition status not checked",
    "Flood and drainage impact not assessed",
]

MANDATORY_ASSUMPTION = "All values are preliminary planning assumptions, not verified engineering design"

MANDATORY_PERMISSIONS = [
    "Local authority building/infrastructure permission",
    "Licensed structural engineer design and certification",
    "Geotechnical soil investigation report",
    "Topographic and utility survey",
    "Environmental clearance (if applicable)",
    "Traffic police / road authority NOC (if applicable)",
]


def enforce(design: dict) -> dict:
    """Force conservative safety content regardless of what the LLM returned."""
    design["required_engineer_review"] = True

    risks = list(design.get("risks") or [])
    for risk in MANDATORY_RISKS:
        if not any(risk.lower()[:20] in r.lower() for r in risks):
            risks.append(risk)
    design["risks"] = risks

    assumptions = list(design.get("assumptions") or [])
    if MANDATORY_ASSUMPTION not in assumptions:
        assumptions.insert(0, MANDATORY_ASSUMPTION)
    design["assumptions"] = assumptions

    permissions = list(design.get("required_permissions") or [])
    for perm in MANDATORY_PERMISSIONS:
        if perm not in permissions:
            permissions.append(perm)
    design["required_permissions"] = permissions
    return design
