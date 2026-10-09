"""Provider-neutral runtime seam and deterministic routing over bounded metadata."""
from dataclasses import dataclass
from typing import Protocol, Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field
from app.core.config import settings


class AssistantProviderError(ValueError):
    def __init__(self, code: str, diagnostics: dict | None = None):
        self.code = code
        self.diagnostics = diagnostics or {}
        super().__init__(code)


class RoutingMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    intent: Literal["QUESTION","SITE_QUERY","DESIGN_REQUEST","CHANGE_REQUEST","ANALYSIS_REQUEST","EXPLANATION_REQUEST","PROPOSAL_APPROVAL","GENERAL_DISCUSSION","CLASSIFY"]
    requested_effect: Literal["READ_ONLY","PROPOSAL_ONLY","APPROVAL_UI_REQUIRED","GENERATE","CALCULATE"] = "READ_ONLY"
    asset_count: Annotated[int,Field(ge=0,le=100)] = 0
    asset_families: Annotated[list[Annotated[str,Field(max_length=64)]],Field(max_length=100)] = Field(default_factory=list)
    tool_requirement: bool = False
    context_size: Annotated[int,Field(ge=0,le=100000)] = 0
    complexity: Literal["SIMPLE","COMPLEX"] = "SIMPLE"
    retry_state: bool = False
    tool_count: Annotated[int,Field(ge=0,le=8)] | None = None
    engineering_sensitive: bool = False
    uncertain: bool = False


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str
    tier: Literal["FAST","PRIMARY","VISION","SPECIALIST"]
    tool_calling_allowed: bool
    max_output_tokens: int
    timeout: float


class ModelRouter:
    def route(self, metadata: RoutingMetadata) -> ModelRoute:
        if metadata.requested_effect in {"GENERATE", "CALCULATE"}:
            raise ValueError("DETERMINISTIC_EXECUTION_ONLY")
        primary = (metadata.requested_effect != "READ_ONLY" or metadata.asset_count > 1 or
            metadata.intent in {"DESIGN_REQUEST","CHANGE_REQUEST","ANALYSIS_REQUEST","PROPOSAL_APPROVAL","CLASSIFY"} or
            metadata.engineering_sensitive or metadata.uncertain or 'CUSTOM' in metadata.asset_families or
            metadata.complexity == "COMPLEX" or (metadata.tool_requirement and metadata.tool_count != 1) or
            (metadata.tool_count or 0)>1 or metadata.retry_state or metadata.context_size > 16000)
        primary = primary or not settings.NEBIUS_FAST_MODEL.strip()
        tier = "PRIMARY" if primary else "FAST"
        primary_model=settings.NEBIUS_PRIMARY_MODEL.strip() or settings.NEBIUS_CHAT_MODEL
        model = primary_model if primary else settings.NEBIUS_FAST_MODEL.strip()
        return ModelRoute("nebius", model, tier, metadata.tool_requirement, 3500 if primary else 2000, 25)


def request_routing_hints(text):
    """Conservative deterministic request guards, never an LLM routing decision."""
    import re
    single_selection=bool(re.fullmatch(r'\s*what objects (?:do i (?:currently )?have selected|are (?:currently )?selected)\s*\?\s*',text,re.I))
    return {'engineering_sensitive':bool(re.search(r'\b(safe|safety|structural|engineering|soil|foundation|bearing|loads?|capacity|slope|terrain|survey|seismic|flood)\b',text,re.I)),
            'uncertain':bool(re.search(r'\b(capability|capabilities|unknown|uncertain|unsupported|available|supported|generate|modify|delete|move|build|create)\b',text,re.I)),
            'tool_count':1 if single_selection else None,'tool_requirement':single_selection}


class AIProvider(Protocol):
    async def complete(self, system: str, payload: dict, route: ModelRoute) -> dict: ...


class NebiusProvider:
    def __init__(self, usage_sink=None, metadata_sink=None):
        self.usage_sink = usage_sink
        self.metadata_sink = metadata_sink if metadata_sink is not None else []

    async def complete(self, system, payload, route):
        from app.services.ai.nebius import assistant_json
        options = {"usage_sink": self.usage_sink} if self.usage_sink is not None else {}
        options["metadata_sink"] = self.metadata_sink
        before = len(self.metadata_sink)
        try:
            return await assistant_json(system, payload, model=route.model, max_output_tokens=route.max_output_tokens, timeout=route.timeout, **options)
        except AssistantProviderError as exc:
            if len(self.metadata_sink) == before:
                self.metadata_sink.append({"http_status":exc.diagnostics.get("httpStatus"),
                    "provider_status":exc.code,"failure_class":"PROVIDER_ERROR" if exc.code != "INVALID_RESPONSE" else "INVALID_STRUCTURED_OUTPUT"})
            raise


class FixtureProvider:
    """Adapts existing deterministic test callables; no network or fallback replies."""
    def __init__(self, callback): self.callback = callback
    async def complete(self, system, payload, route): return await self.callback(system, payload)
