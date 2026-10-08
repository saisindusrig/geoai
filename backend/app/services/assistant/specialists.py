"""One execution interface. Production registry intentionally has no new adapters."""
from dataclasses import dataclass
from typing import Protocol, Any
from pydantic import BaseModel
from app.core.asset_families import FAMILIES, asset_definition


@dataclass(frozen=True)
class AdapterMetadata:
    id: str
    version: str
    asset_family: str
    supported_asset_types: frozenset[str]
    capabilities: frozenset[str]
    specification_schema_version: str
    patch_operations: frozenset[str] = frozenset()


class SpecialistAdapter(Protocol):
    metadata: AdapterMetadata
    specification_schema: type[BaseModel]

    def can_handle(self, asset_type: str) -> bool: ...
    def requirements_to_specification(self, requirements: BaseModel, context: BaseModel) -> BaseModel: ...
    def validate_specification(self, specification: BaseModel) -> BaseModel: ...
    def generate_preview(self, specification: BaseModel) -> BaseModel: ...
    def generate(self, specification: BaseModel) -> BaseModel: ...
    def validate_geometry(self, geometry: BaseModel, specification: BaseModel) -> BaseModel: ...
    def apply_patch(self, model: BaseModel, patch: BaseModel) -> BaseModel: ...


class AdapterRegistry:
    def __init__(self):
        self._adapters: dict[str, SpecialistAdapter] = {}

    def register(self, adapter: SpecialistAdapter):
        m=adapter.metadata
        if m.id in self._adapters or m.asset_family not in FAMILIES or not m.version or not m.specification_schema_version:
            raise ValueError("INVALID_ADAPTER_REGISTRATION")
        if not m.capabilities <= {"DISCUSS","PLAN","PROPOSE","GENERATE","VALIDATE_GEOMETRY","ANALYZE"}:
            raise ValueError("INVALID_ADAPTER_CAPABILITY")
        if not issubclass(adapter.specification_schema,BaseModel):raise ValueError("TYPED_SPECIFICATION_REQUIRED")
        required=("can_handle","requirements_to_specification","validate_specification","generate_preview","generate","validate_geometry","apply_patch")
        if not all(callable(getattr(adapter,name,None)) for name in required):raise ValueError("INCOMPLETE_ADAPTER")
        self._adapters[m.id]=adapter

    def resolve(self, asset_type: str):
        family=asset_definition(asset_type)["family"]
        candidates=[a for a in self._adapters.values() if a.metadata.asset_family==family
            and (not a.metadata.supported_asset_types or asset_type.lower() in {s.lower() for s in a.metadata.supported_asset_types}) and a.can_handle(asset_type)]
        # Prefer an explicit type adapter over a family-wide adapter, never LLM class names.
        specific=[a for a in candidates if a.metadata.supported_asset_types]
        candidates=specific or candidates
        if len(candidates)>1:raise ValueError("AMBIGUOUS_ADAPTER")
        return candidates[0] if candidates else None


ADAPTERS=AdapterRegistry()


def route_assets(assets: list[dict], registry=ADAPTERS):
    results=[]
    for asset in assets:
        definition=asset_definition(asset["assetType"])
        adapter=registry.resolve(asset["assetType"])
        supported=bool(adapter and "GENERATE" in adapter.metadata.capabilities)
        results.append({"assetRequestId":asset["assetRequestId"],"assetType":asset["assetType"],"assetFamily":definition["family"],
            "status":"SUPPORTED" if supported else "UNSUPPORTED","adapterId":adapter.metadata.id if supported else None,
            "adapterVersion":adapter.metadata.version if supported else None,"specificationSchemaVersion":adapter.metadata.specification_schema_version if supported else None,
            "reason":None if supported else "No registered specialist execution adapter supports this asset."})
    count=sum(r["status"]=="SUPPORTED" for r in results)
    return {"status":"SUPPORTED" if results and count==len(results) else "PARTIAL" if count else "UNSUPPORTED","assets":results,
        "atomicApproval":True,"canBuildAll":bool(results) and count==len(results)}


class ExecutionRouter:
    def __init__(self,registry=ADAPTERS):self.registry=registry

    def route_approved(self,db,project_id,version_id):
        from app.services.assistant.storage import lock_project
        from app.services.assistant.proposals import ProposalService
        lock_project(db,project_id)
        proposal=ProposalService().assert_build_current(db,project_id,version_id)
        entries=proposal["content"].get("assetProposals") or [{"assetRequestId":str(i),"assetType":a["assetType"]} for i,a in enumerate(proposal["content"]["request"]["assets"])]
        return route_assets(entries,self.registry)
