"""Pydantic schemas for deterministic design engineering validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ValidationWarning(BaseModel):
    code: str
    message: str
    field: str | None = None


class ValidationError(BaseModel):
    code: str
    message: str
    field: str | None = None


class DesignRecommendation(BaseModel):
    code: str
    message: str


class DesignValidationResult(BaseModel):
    validation_status: Literal["pass", "warning", "fail"]
    score: int = Field(ge=0, le=100)
    warnings: list[ValidationWarning] = Field(default_factory=list)
    errors: list[ValidationError] = Field(default_factory=list)
    recommendations: list[DesignRecommendation] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    conceptual_disclaimer: str = ""

    def to_dict(self) -> dict:
        return self.model_dump()
