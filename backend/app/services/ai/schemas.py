"""Pydantic schema the AI design output MUST validate against."""

from pydantic import BaseModel, Field


class DesignLayer(BaseModel):
    name: str
    description: str = ""


class DesignOutput(BaseModel):
    project_type: str
    summary: str
    assumptions: list[str] = Field(min_length=1)
    geometry: dict  # type-specific keys (length_m, deck_width_m, floors, ...)
    materials: dict = {}
    layers: list[DesignLayer] = []
    construction_sequence: list[str] = Field(min_length=3)
    risks: list[str] = Field(min_length=1)
    required_engineer_review: bool = True
    required_permissions: list[str] = []
