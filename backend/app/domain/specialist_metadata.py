"""Provider-independent specialist registration metadata."""
from dataclasses import dataclass

@dataclass(frozen=True)
class AdapterMetadata:
    id: str
    version: str
    asset_family: str
    supported_asset_types: frozenset[str]
    capabilities: frozenset[str]
    specification_schema_version: str
    patch_operations: frozenset[str] = frozenset()
