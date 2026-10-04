"""Strict Pydantic schemas for LLM design parameter planning (no mesh geometry)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ProjectType = Literal["flyover", "road", "building", "pipeline", "bridge", "layout"]


class DesignAssumption(BaseModel):
    text: str = Field(min_length=3, max_length=500)


class DesignWarning(BaseModel):
    text: str = Field(min_length=3, max_length=500)


class MissingInput(BaseModel):
    field: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=3, max_length=300)


class DesignParameters(BaseModel):
    """Numeric / boolean planning parameters only — never 3D mesh data."""

    lanes: int | None = Field(None, ge=1, le=12)
    lane_width_m: float | None = Field(None, ge=2.5, le=5.0)
    total_width_m: float | None = Field(None, ge=3.0, le=60.0)
    length_m: float | None = Field(None, ge=50.0, le=100_000.0)
    clearance_m: float | None = Field(None, ge=4.0, le=12.0)
    pier_spacing_m: float | None = Field(None, ge=15.0, le=60.0)
    deck_depth_m: float | None = Field(None, ge=0.3, le=2.0)
    deck_width_m: float | None = Field(None, ge=6.0, le=60.0)
    road_width_m: float | None = Field(None, ge=3.0, le=40.0)
    shoulder_width_m: float | None = Field(None, ge=0.0, le=5.0)
    asphalt_thickness_mm: float | None = Field(None, ge=40.0, le=150.0)
    base_thickness_mm: float | None = Field(None, ge=100.0, le=500.0)
    foundation_depth_m_assumed: float | None = Field(None, ge=3.0, le=40.0)
    drainage_required: bool | None = None
    service_roads_required: bool | None = None
    builtup_area_sqm: float | None = Field(None, ge=50.0, le=100_000.0)
    floors: int | None = Field(None, ge=1, le=60)
    floor_height_m: float | None = Field(None, ge=2.5, le=6.0)
    pipe_diameter_mm: float | None = Field(None, ge=100.0, le=3000.0)
    trench_width_m: float | None = Field(None, ge=0.6, le=5.0)
    trench_depth_m: float | None = Field(None, ge=0.8, le=10.0)
    concrete_grade: str | None = Field(None, max_length=20)
    utility_type: str | None = Field(None, max_length=40)

    @field_validator("concrete_grade", "utility_type", mode="before")
    @classmethod
    def strip_strings(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip() or None
        return v


class DesignPlan(BaseModel):
    """LLM output: planning parameters and notes only."""

    project_type: str
    parameters: DesignParameters = Field(default_factory=DesignParameters)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    warnings: list[str] = Field(default_factory=list, max_length=20)
    missing_inputs: list[MissingInput] = Field(default_factory=list, max_length=15)

    @model_validator(mode="after")
    def normalize_lists(self) -> DesignPlan:
        self.assumptions = [a.strip() for a in self.assumptions if a and a.strip()]
        self.warnings = [w.strip() for w in self.warnings if w and w.strip()]
        return self

    @field_validator("project_type")
    @classmethod
    def normalize_project_type(cls, v: str) -> str:
        return (v or "").strip().lower()


FAMILY_ALIASES: dict[str, str] = {
    "bridge": "flyover",
    "layout": "road",
}

DEFAULTS_BY_FAMILY: dict[str, dict[str, float | int | str | bool]] = {
    "flyover": {
        "lanes": 4,
        "lane_width_m": 3.65,
        "deck_width_m": 16.0,
        "clearance_m": 5.5,
        "pier_spacing_m": 30.0,
        "deck_depth_m": 0.6,
        "foundation_depth_m_assumed": 8.0,
        "asphalt_thickness_mm": 80,
        "concrete_grade": "M35",
        "drainage_required": True,
    },
    "road": {
        "lanes": 2,
        "lane_width_m": 3.5,
        "road_width_m": 7.5,
        "shoulder_width_m": 1.5,
        "asphalt_thickness_mm": 80,
        "base_thickness_mm": 250,
        "drainage_required": True,
    },
    "building": {
        "floors": 4,
        "floor_height_m": 3.2,
        "builtup_area_sqm": 400.0,
        "concrete_grade": "M25",
    },
    "pipeline": {
        "pipe_diameter_mm": 600,
        "trench_width_m": 1.2,
        "trench_depth_m": 2.0,
        "utility_type": "drainage",
        "drainage_required": True,
    },
}
