"""BIM V1 to isolated CAD candidate. Never imported by production execution.

V1 primitives cannot express holes/lofts: an explicit versioned CAD recipe
sidecar supplies bounded operations. The V1 primitive is a legacy envelope
descriptor, not executed or silently substituted for this recipe's CAD solid.
"""
from dataclasses import dataclass
from copy import deepcopy
import hashlib
import json
from typing import Annotated, Literal
from pydantic import Field
from app.domain.stage1 import Contract, Id
from app.domain.bim import BIMProject, GeometryDefinition
from app.services.assistant.bim_foundation import validate_foundation, propagate_parameters


class CADRecipe(Contract):
    component_id: Id
    operation: Literal["PROFILE_EXTRUSION", "CIRCULAR_COLUMN", "RECTANGULAR_OPENING", "CIRCULAR_HOLE", "RECTANGULAR_LOFT"]
    orientation: Literal["VERTICAL", "HORIZONTAL"] = "VERTICAL"


class CADMapping(Contract):
    schema_version: Literal["cad-proof/1"] = "cad-proof/1"
    legacy_primitive_policy: Literal["NOT_EXECUTED"] = "NOT_EXECUTED"
    recipes: Annotated[list[CADRecipe], Field(min_length=1, max_length=250)]


@dataclass(frozen=True)
class TrustedSource:
    """Server/caller-owned context, separate from the authored BIM payload."""
    design_id: str
    design_version: int
    source_model_revision_id: str | None


@dataclass(frozen=True)
class Candidate:
    model: BIMProject
    mapping: CADMapping
    outputs: dict
    epoch: int = 1


def metre_parameters(parameters):
    values = {}
    for parameter in parameters:
        if parameter.unit != "m":
            raise ValueError("CAD_METRE_PARAMETERS_REQUIRED")
        values[parameter.id] = parameter.value
    return values


def require(values, keys):
    if set(values) != set(keys):
        raise ValueError("UNSUPPORTED_CAD_PARAMETERS")
    from app.experimental import cad_geometry as cad
    cad.positive(*values.values())


def compile_component(model, component, recipe):
    from app.experimental import cad_geometry as cad
    params = metre_parameters(component.parameters)
    section_id = component.geometry.cross_section_id
    section = next((s for s in model.cross_sections if s.id == section_id), None)
    if recipe.operation == "PROFILE_EXTRUSION":
        require(params, ["length"])
        if section is None:
            raise ValueError("CROSS_SECTION_REQUIRED")
        values = metre_parameters(section.parameters)
        if section.profile == "RECTANGLE":
            require(values, ["width", "depth"])
            points = cad.rectangle(values["width"], values["depth"])
        elif section.profile == "I":
            require(values, ["width", "depth", "web", "flange"])
            points = cad.i_profile(values["width"], values["depth"], values["web"], values["flange"])
        else:
            raise ValueError("UNSUPPORTED_CAD_PROFILE")
        solid = cad.extrude(points, params["length"])
    elif recipe.operation == "CIRCULAR_COLUMN":
        require(params, ["length"])
        if section is None or section.profile != "CIRCLE":
            raise ValueError("CIRCLE_SECTION_REQUIRED")
        values = metre_parameters(section.parameters)
        require(values, ["radius"])
        solid = cad.circular_column(values["radius"], params["length"])
    elif recipe.operation == "RECTANGULAR_OPENING":
        require(params, ["width", "depth", "thickness", "hole_width", "hole_depth"])
        solid = cad.box_with_opening(**params)
    elif recipe.operation == "CIRCULAR_HOLE":
        require(params, ["width", "depth", "thickness", "hole_radius"])
        solid = cad.box_with_opening(**params)
    elif recipe.operation == "RECTANGULAR_LOFT":
        require(params, ["width", "depth", "end_width", "end_depth", "length"])
        solid = cad.tapered_rectangle(**params)
    else:
        raise ValueError("UNSUPPORTED_CAD_OPERATION")
    if component.geometry.primitive.primitive_type != "BOX":
        raise ValueError("CAD_LEGACY_ENVELOPE_REQUIRED")
    solid = cad.transform(solid, (0,0,0), horizontal=recipe.orientation == "HORIZONTAL")
    bounds = cad.solid_metrics(solid)["boundsM"]
    # Keep V1's mandatory legacy envelope consistent, including regeneration.
    # It is explicitly NOT_EXECUTED; openings/sections live in the CAD recipe.
    envelope = GeometryDefinition.model_validate(dict(cross_section_id=section_id,primitive=dict(
        primitive_type="BOX",center=[(bounds[i]+bounds[i+3])/2 for i in range(3)],
        size=[bounds[i+3]-bounds[i] for i in range(3)])))
    component = component.model_copy(update={"geometry":envelope})
    assembly = next(a for a in model.assemblies if a.id == component.assembly_id)
    solid = cad.transform(solid, component.placement.origin, component.placement.heading_deg)
    solid = cad.transform(solid, assembly.placement.origin, assembly.placement.heading_deg)
    definition = {"component": component.model_dump(mode="json", by_alias=True), "legacyPrimitivePolicy": "NOT_EXECUTED",
                  "assemblyPlacement": assembly.placement.model_dump(mode="json", by_alias=True),
                  "crossSection": section.model_dump(mode="json", by_alias=True) if section else None,
                  "recipe": recipe.model_dump(mode="json", by_alias=True), "kernel": "OCCT/OCP-8.0.1.1.0"}
    digest = hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"id": component.id, "assetId": component.asset_id, "assemblyId": component.assembly_id,
            "materialId": component.material_id, "definition": definition, "definitionHash": digest,
            "provenance": component.provenance.model_dump(mode="json", by_alias=True),
            "dependencyIds": list(component.dependency_ids), "frame": "LOCAL_VISUAL_REFERENCE", "units": "m",
            "engineeringStatus": "UNVERIFIED", "metrics": cad.solid_metrics(solid), "mesh": cad.tessellate(solid)}


def checked_inputs(model, mapping, trusted):
    model, _ = validate_foundation(model)
    mapping = CADMapping.model_validate(mapping)
    recipe_ids = [r.component_id for r in mapping.recipes]
    if len(recipe_ids) != len(set(recipe_ids)) or set(recipe_ids) != {c.id for c in model.components}:
        raise ValueError("CAD_RECIPE_MEMBERSHIP_MISMATCH")
    for c in model.components:
        p = c.provenance
        if (p.design_id, p.design_version, p.source_model_revision_id) != (trusted.design_id, trusted.design_version, trusted.source_model_revision_id):
            raise ValueError("UNTRUSTED_CAD_SOURCE")
    return model, mapping


def build_candidate(model, mapping, *, trusted):
    model, mapping = checked_inputs(model, mapping, trusted)
    components = {c.id: c for c in model.components}
    outputs = {}
    for recipe in mapping.recipes:
        outputs[recipe.component_id] = compile_component(model,components[recipe.component_id],recipe)
        check_mesh_budget(outputs)
    return Candidate(canonical_model(model,outputs,set(outputs)), mapping, outputs)


def canonical_model(model, outputs, dirty):
    raw = model.model_dump(mode="json",by_alias=True)
    raw["components"] = [outputs[c.id]["definition"]["component"] if c.id in dirty else c.model_dump(mode="json",by_alias=True) for c in model.components]
    return BIMProject.model_validate(raw)


def check_mesh_budget(outputs):
    if sum(len(o["mesh"]["positions"]) for o in outputs.values()) > 250000 or sum(len(o["mesh"]["triangles"]) for o in outputs.values()) > 500000:
        raise ValueError("CANDIDATE_MESH_LIMIT")


def regenerate(candidate, changes, *, trusted):
    model, mapping = checked_inputs(candidate.model, candidate.mapping, trusted)
    updated, dirty = propagate_parameters(model, changes, expected_design_version=trusted.design_version)
    # Construct everything affected before publishing a new detached candidate.
    outputs = deepcopy(candidate.outputs)
    components = {c.id: c for c in updated.components}
    recipes = {r.component_id: r for r in mapping.recipes}
    rebuilt = {id: compile_component(updated, components[id], recipes[id]) for id in dirty}
    outputs.update(rebuilt)
    check_mesh_budget(outputs)
    return Candidate(canonical_model(updated,outputs,set(dirty)), mapping, outputs, candidate.epoch+1), dirty
