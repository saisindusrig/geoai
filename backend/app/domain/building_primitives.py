"""Pure bounded building primitives shared by legacy planning and specialist V1."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

Number = Annotated[float, Field(ge=-1000, le=1000, allow_inf_nan=False)]
Dimension = Annotated[float, Field(gt=0, le=200, allow_inf_nan=False)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PlanValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("The proposed layout needs revision: " + " ".join(errors[:8]))


class Rectangle(StrictModel):
    x: Number
    y: Number
    width: Dimension
    depth: Dimension


class Room(Rectangle):
    id: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=100)
    floor: int = Field(ge=0, le=9)


class Wall(StrictModel):
    id: str = Field(min_length=1, max_length=60)
    floor: int = Field(ge=0, le=9)
    start: tuple[Number, Number]
    end: tuple[Number, Number]
    thickness: float = Field(default=0.15, ge=0.08, le=0.5)


class Opening(StrictModel):
    id: str = Field(min_length=1, max_length=60)
    wall_id: str
    kind: Literal["door", "window"]
    offset: float = Field(ge=0, le=200)
    width: float = Field(gt=0, le=5)
    height: float = Field(gt=0, le=4)
    sill: float = Field(ge=0, le=3)


class Column(StrictModel):
    x: Number
    y: Number
    size: float = Field(default=0.3, ge=0.2, le=1)


class Beam(StrictModel):
    start: tuple[Number, Number]
    end: tuple[Number, Number]
    width: float = Field(default=0.25, ge=0.15, le=1)
    depth: float = Field(default=0.35, ge=0.2, le=1)

