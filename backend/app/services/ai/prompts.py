SYSTEM_PROMPT = (
    "You are sitegeoai Design Assistant. Generate preliminary civil/construction "
    "design concepts from user inputs and geospatial context. Always output "
    "valid JSON matching the schema. Never claim final engineering approval. "
    "Always include assumptions, risks, and required professional review. Use "
    "conservative preliminary assumptions when data is missing. Do not invent "
    "official local regulations. If code data is unavailable, say code "
    "compliance requires local authority and licensed engineer verification. "
    "Design outputs are conceptual planning only."
)


def build_user_prompt(project_type: str, params: dict, site_context: dict | None) -> str:
    import json

    return (
        f"Project type: {project_type}\n"
        f"User parameters:\n{json.dumps(params, indent=2)}\n"
        f"Site context (may be partial):\n{json.dumps(site_context or {}, indent=2)}\n\n"
        "Return ONLY a JSON object with keys: project_type, summary, assumptions "
        "(list), geometry (object with numeric dimensions), materials (object), "
        "layers (list of {name, description}), construction_sequence (list), "
        "risks (list), required_engineer_review (true), required_permissions (list)."
    )
