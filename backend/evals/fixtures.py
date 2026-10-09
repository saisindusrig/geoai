"""Uses production argument contracts, never production tool execution or SQL."""
import json
from copy import deepcopy
from pydantic import ValidationError
from app.services.assistant.tool_contracts import SCHEMAS, envelope


class FixtureTools:
    def __init__(self, case):
        self.case = case
        self.calls = []
        self.failures = []
        self.semantic_failures = []
        self.effect_mismatches = []
        self.results = []

    def describe(self):
        return [{"name": name, "argumentsSchema": SCHEMAS[name].model_json_schema(by_alias=True)}
                for name in self.case.fixtures]

    def execute(self, name, arguments):
        self.calls.append({"name": name, "arguments": arguments})
        def deny(code):
            self.failures.append(code)
            return envelope("DENIED", code=code)
        if len(self.calls) > 8:
            return deny("TOOL_LIMIT")
        if name not in SCHEMAS or name not in self.case.fixtures:
            return deny("UNSUPPORTED_TOOL")
        try:
            raw = json.loads(arguments)
            if not isinstance(raw, dict):
                return deny("MALFORMED_TOOL_ARGUMENTS")
            if any(key in raw for key in ("projectId", "project_id", "actorId", "tenantId")):
                return deny("AUTHORITY_VIOLATION")
            parsed = SCHEMAS[name].model_validate(raw)
        except (ValueError, TypeError, ValidationError):
            return deny("MALFORMED_TOOL_ARGUMENTS")
        if name in {"create_proposal", "revise_proposal"}:
            if self.case.expected.allowedEffect != "PROPOSAL_ONLY":
                return deny("FORBIDDEN_MUTATION")
            targets = parsed.translation.object_ids if parsed.translation else []
            selected = self.case.context.get("selected_objects", [])
            if any(obj not in selected for obj in targets):
                return deny("AUTHORITY_VIOLATION")
        if name == "validate_proposal" and parsed.proposal_version_id not in self.case.context.get("proposal_ids", []):
            return deny("AUTHORITY_VIOLATION")
        if name == "revise_proposal" and parsed.parent_version_id not in self.case.context.get("proposal_ids", []):
            return deny("AUTHORITY_VIOLATION")
        result = deepcopy(self.case.fixtures[name])
        if name == "sample_terrain" and isinstance(result.get("data"), list):
            result["data"] = result["data"][:parsed.sample_count]
        self.results.append({"name":name,"result":deepcopy(result)})
        return result
