from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.domain.stage1 import CivilIntent
from app.domain.assistant_runtime import ProviderResponse


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class EvaluationResponse(Strict):
    intent: CivilIntent
    response: ProviderResponse
    effect: Literal["READ_ONLY", "PROPOSAL_ONLY", "APPROVAL_UI_REQUIRED"]
    facts: dict[str, str | float | None]
    missing_data: list[str]
    claims: list[Literal["STRUCTURAL_SAFETY", "GENERATOR_AVAILABLE", "MODEL_MUTATED"]]
    relationships: list[str]


class Expected(Strict):
    intent: Literal["QUESTION", "SITE_QUERY", "DESIGN_REQUEST", "CHANGE_REQUEST", "ANALYSIS_REQUEST", "EXPLANATION_REQUEST", "PROPOSAL_APPROVAL", "GENERAL_DISCUSSION"]
    assets: list[str]
    asset_counts: dict[str, int] = Field(default_factory=dict)
    mustAskClarification: bool
    mustNotClaimEngineeringSafety: bool = True
    allowedEffect: Literal["READ_ONLY", "PROPOSAL_ONLY", "APPROVAL_UI_REQUIRED"]
    required_tools: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    facts: dict[str, str | float | None] = Field(default_factory=dict)
    object_ids: list[str] = Field(default_factory=list)
    delta_m: list[float] | None = None
    relationships: list[str] = Field(default_factory=list)


class Case(Strict):
    id: str
    category: Literal["SIMPLE_CONVERSATION", "ASSET_UNDERSTANDING", "MULTI_ASSET", "AMBIGUOUS", "SITE_AWARE", "UNKNOWN_DATA", "CAPABILITY_LIMITS", "MODEL_EDITING", "RELATIONSHIPS", "UNUSUAL_ASSETS"]
    userMessage: str
    context: dict
    fixtures: dict[str, dict]
    expected: Expected


class Candidate(Strict):
    key: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,40}$")
    display_name: str
    model_id: str | None
    verified: bool = False
    availability: Literal["UNKNOWN", "AVAILABLE", "UNAVAILABLE"] = "UNKNOWN"
    availability_note: str | None = None
    input_per_million: float | None = Field(default=None, ge=0)
    output_per_million: float | None = Field(default=None, ge=0)
    pricing_source: str | None = None

    @model_validator(mode="after")
    def verified_id(self):
        if self.model_id is not None and (not self.model_id.strip() or self.model_id != self.model_id.strip()):
            raise ValueError("Model ID must be a nonempty exact provider ID")
        if self.verified and not self.model_id:
            raise ValueError("Verified candidate needs a provider model ID")
        if self.availability == "UNAVAILABLE" and self.verified:
            raise ValueError("Unavailable candidate cannot be verified")
        if (self.input_per_million is not None or self.output_per_million is not None) and not self.pricing_source:
            raise ValueError("Pricing needs a documented source")
        return self


class ModelConfig(Strict):
    version: Literal["geoai-eval/1"]
    max_output_tokens: int = Field(default=3500, ge=100, le=16000)
    timeout: float = Field(default=25, gt=0, le=120)
    max_rounds: int = Field(default=3, ge=1, le=5)
    repairs: int = Field(default=1, ge=0, le=1)
    candidates: list[Candidate]
    catalogue_verification: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_keys(self):
        if len({c.key for c in self.candidates}) != len(self.candidates):
            raise ValueError("Duplicate candidate keys")
        return self
