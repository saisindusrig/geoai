"""Lean AI-authored design data. Persisted AI3DDesign remains unchanged."""
from typing import Annotated
from pydantic import Field, TypeAdapter
from app.domain.stage1 import Contract, Id
from app.domain.ai3d import DesignSystem, DesignObject, DesignRelationship, DesignConstraint
from app.domain.building_specialist import PreviewAssumption
from app.domain.assistant_runtime import ProposalToolArguments

UNKNOWN_FIELDS=['groundElevation','soil','soilBearingCapacity','groundwater','surveyAccuracy','utilityLocations','designLoads','structuralCapacity','foundations','codeCompliance','engineeringApproval']

class DesignIntent(Contract):
    systems: Annotated[list[DesignSystem],Field(min_length=1,max_length=20)]
    objects: Annotated[list[DesignObject],Field(min_length=1,max_length=250)]
    relationships: Annotated[list[DesignRelationship],Field(max_length=100)]=Field(default_factory=list)
    constraints: Annotated[list[DesignConstraint],Field(max_length=100)]=Field(default_factory=list)
    assumptions: Annotated[list[PreviewAssumption],Field(min_length=1,max_length=20)]
    unknowns: Annotated[list[Id],Field(max_length=50)]=Field(default_factory=lambda:list(UNKNOWN_FIELDS))

class GenericProposalArguments(Contract):
    design: DesignIntent

class ProposalArguments:
    """Compatibility parser: lean generic input or existing specialist contracts."""
    @classmethod
    def model_validate(cls,value):
        return TypeAdapter(GenericProposalArguments | ProposalToolArguments).validate_python(value)
    @classmethod
    def model_json_schema(cls,**kwargs):
        return TypeAdapter(GenericProposalArguments | ProposalToolArguments).json_schema(**kwargs)
