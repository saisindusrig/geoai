"""Data-only CAD contract. No native imports or production Build registration."""
import hashlib
import json
from typing import Annotated, Literal
from pydantic import Field, model_validator
from app.domain.stage1 import Contract, Id, Digest, Finite
from app.domain.bim import Placement, SourceProvenance, Dependency, Connection, Material

Positive = Annotated[float, Field(ge=.0001, le=500, allow_inf_nan=False, strict=True)]
Ids = Annotated[list[Id], Field(max_length=250)]


def encode(value):
    if isinstance(value, Contract):
        value = value.model_dump(mode="json", by_alias=True)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


class Recipe(Contract):
    version: Literal["cad-recipe/1"] = "cad-recipe/1"
    operation: Literal["PROFILE_EXTRUSION", "CIRCULAR_COLUMN", "RECTANGULAR_OPENING", "CIRCULAR_HOLE", "RECTANGULAR_LOFT"]
    orientation: Literal["VERTICAL", "HORIZONTAL"] = "VERTICAL"
    profile: Literal["RECTANGLE", "I", "CIRCLE"] | None = None
    # A closed operation-specific parameter vocabulary, all SI metres.
    parameters: Annotated[dict[Id, Positive], Field(min_length=1, max_length=9)]
    units: Literal["m"] = "m"

    @model_validator(mode="after")
    def valid_recipe(self):
        p = self.parameters
        profiles = {"RECTANGLE": {"width", "depth"}, "I": {"width", "depth", "web", "flange"}, "CIRCLE": {"radius"}}
        if self.operation == "PROFILE_EXTRUSION":
            if self.profile not in ("RECTANGLE", "I"):
                raise ValueError("UNSUPPORTED_PROFILE")
            keys = profiles[self.profile] | {"length"}
        elif self.operation == "CIRCULAR_COLUMN":
            if self.profile != "CIRCLE":
                raise ValueError("CIRCLE_REQUIRED")
            keys = {"radius", "length"}
        else:
            if self.profile is not None:
                raise ValueError("UNEXPECTED_PROFILE")
            keys = {"RECTANGULAR_OPENING": {"width", "depth", "thickness", "hole_width", "hole_depth"}, "CIRCULAR_HOLE": {"width", "depth", "thickness", "hole_radius"}, "RECTANGULAR_LOFT": {"width", "depth", "end_width", "end_depth", "length"}}[self.operation]
        if set(p) != keys:
            raise ValueError("PARAMETER_VOCABULARY_MISMATCH")
        if self.profile == "I" and (p["web"] >= p["width"] or 2*p["flange"] >= p["depth"]):
            raise ValueError("INVALID_I_SECTION")
        if self.operation == "RECTANGULAR_OPENING" and (p["hole_width"] >= p["width"] or p["hole_depth"] >= p["depth"]):
            raise ValueError("OPENING_OUTSIDE_FACE")
        if self.operation == "CIRCULAR_HOLE" and 2*p["hole_radius"] >= min(p["width"], p["depth"]):
            raise ValueError("HOLE_OUTSIDE_FACE")
        return self


class Definition(Contract):
    component_id: Id
    asset_id: Id
    assembly_id: Id
    component_type: Id
    material: Material
    recipe: Recipe
    placement: Placement
    assembly_placement: Placement
    dependency_ids: Ids
    relationship_ids: Ids
    provenance: SourceProvenance
    units: Literal["m"] = "m"
    frame: Literal["PROJECT_LOCAL_VISUAL_REFERENCE"] = "PROJECT_LOCAL_VISUAL_REFERENCE"


class Source(Contract):
    project_id: Annotated[int, Field(strict=True, gt=0)]
    revision_id: Annotated[int, Field(strict=True, gt=0)]
    revision_document_hash: Digest
    design_id: Id
    design_version: Annotated[int, Field(strict=True, gt=0)]
    source_model_revision_id: Id | None


class Geometry(Contract):
    schema_version: Literal["cad-geometry/1"] = "cad-geometry/1"
    source: Source
    definitions: Annotated[list[Definition], Field(min_length=1, max_length=250)]
    dependencies: Annotated[list[Dependency], Field(max_length=250)] = []
    connections: Annotated[list[Connection], Field(max_length=250)] = []
    compiler_version: Literal["cad-compiler/1"] = "cad-compiler/1"
    kernel: Literal["cadquery-ocp/8.0.1.1.0"] = "cadquery-ocp/8.0.1.1.0"
    mesher_version: Literal["cad-mesh/1:0.002m:0.2rad"] = "cad-mesh/1:0.002m:0.2rad"
    engineering_quantities: Literal["UNAVAILABLE"] = "UNAVAILABLE"

    @model_validator(mode="after")
    def identities(self):
        ids = [d.component_id for d in self.definitions]
        if len(set(ids)) != len(ids):
            raise ValueError("DUPLICATE_COMPONENT")
        for d in self.definitions:
            p = d.provenance
            if (p.design_id, p.design_version, p.source_model_revision_id) != (self.source.design_id, self.source.design_version, self.source.source_model_revision_id):
                raise ValueError("SOURCE_BINDING_MISMATCH")
        for edge in [*self.dependencies, *self.connections]:
            a = getattr(edge, "source_component_id", getattr(edge, "from_component_id", None))
            b = getattr(edge, "target_component_id", getattr(edge, "to_component_id", None))
            if a not in ids or b not in ids:
                raise ValueError("DANGLING_ASSEMBLY_REFERENCE")
        dep_ids = [e.id for e in self.dependencies]
        connection_ids = [e.id for e in self.connections]
        if len(set(dep_ids)) != len(dep_ids) or len(set(connection_ids)) != len(connection_ids):
            raise ValueError("DUPLICATE_RELATIONSHIP")
        definitions = {d.component_id: d for d in self.definitions}
        graph = {i: set() for i in ids}
        writers = set()
        for e in self.dependencies:
            a, b = definitions[e.source_component_id], definitions[e.target_component_id]
            if e.source_parameter_id not in a.recipe.parameters or e.target_parameter_id not in b.recipe.parameters:
                raise ValueError("DANGLING_PARAMETER")
            target = (b.component_id, e.target_parameter_id)
            if target in writers:
                raise ValueError("MULTIPLE_PARAMETER_WRITERS")
            writers.add(target)
            graph[a.component_id].add(b.component_id)
            if e.operation == "COPY" and a.recipe.parameters[e.source_parameter_id] != b.recipe.parameters[e.target_parameter_id]:
                raise ValueError("DEPENDENCY_VALUE_MISMATCH")
        pending = set(ids)
        while pending:
            roots = {i for i in pending if not any(i in graph[j] for j in pending)}
            if not roots:
                raise ValueError("DEPENDENCY_CYCLE")
            pending -= roots
        for d in self.definitions:
            expected_deps = {e.id for e in self.dependencies if d.component_id in (e.source_component_id, e.target_component_id)}
            expected_connections = {e.id for e in self.connections if d.component_id in (e.from_component_id, e.to_component_id)}
            if set(d.dependency_ids) != expected_deps or set(d.relationship_ids) != expected_connections:
                raise ValueError("RELATIONSHIP_MEMBERSHIP_MISMATCH")
        return self


class Artifact(Contract):
    sha256: Digest
    byte_length: Annotated[int, Field(strict=True, gt=0, le=32_000_000)]
    kind: Literal["BREP", "MESH"]


class Result(Contract):
    component_id: Id
    definition_hash: Digest
    brep: Artifact
    mesh: Artifact
    dimensions_m: tuple[Positive, Positive, Positive]
    volume_m3: Annotated[float, Field(gt=0, le=125_000_000, allow_inf_nan=False)]
    bounds_m: tuple[Finite, Finite, Finite, Finite, Finite, Finite]
    solid_count: Literal[1] = 1
    geometry_valid: Literal[True] = True
    engineering_status: Literal["UNVERIFIED"] = "UNVERIFIED"

    @model_validator(mode="after")
    def artifact_kinds(self):
        if self.brep.kind != "BREP" or self.mesh.kind != "MESH":
            raise ValueError("ARTIFACT_KIND_MISMATCH")
        if any(abs((self.bounds_m[i+3]-self.bounds_m[i])-self.dimensions_m[i]) > 1e-6 for i in range(3)):
            raise ValueError("DIMENSION_BOUNDS_MISMATCH")
        return self


class Manifest(Contract):
    schema_version: Literal["cad-artifacts/1"] = "cad-artifacts/1"
    geometry: Geometry
    results: Annotated[list[Result], Field(min_length=1, max_length=250)]

    @model_validator(mode="after")
    def bound_results(self):
        expected = {d.component_id: digest(d) for d in self.geometry.definitions}
        if len(self.results) != len(expected) or {r.component_id:r.definition_hash for r in self.results} != expected:
            raise ValueError("RESULT_BINDING_MISMATCH")
        return self


def cache_key(geometry):
    # Includes immutable revision binding, definitions, compiler and mesher versions.
    return digest(Geometry.model_validate(geometry))


def from_bim(model, mapping, *, source):
    """Source must be constructed from an owned persisted revision by the caller.

    Intentionally excludes the legacy primitive; it cannot affect CAD geometry.
    """
    from app.services.assistant.bim_foundation import validate_foundation
    model, _ = validate_foundation(model)
    recipes = {r.component_id: r for r in mapping.recipes}
    if len(recipes) != len(mapping.recipes) or set(recipes) != {c.id for c in model.components}:
        raise ValueError("RECIPE_MEMBERSHIP_MISMATCH")
    definitions = []
    for c in model.components:
        r = recipes[c.id]
        s = next((s for s in model.cross_sections if s.id == c.geometry.cross_section_id), None)
        params = [*c.parameters, *(s.parameters if s else [])]
        if any(p.unit != "m" for p in params) or len({p.id for p in params}) != len(params):
            raise ValueError("METRE_PARAMETERS_REQUIRED")
        definitions.append(Definition(component_id=c.id, asset_id=c.asset_id, assembly_id=c.assembly_id,
            component_type=c.component_type, material=next(m for m in model.materials if m.id == c.material_id),
            recipe=Recipe(operation=r.operation, orientation=r.orientation, profile=s.profile if s else None,
                          parameters={p.id: p.value for p in params}), placement=c.placement,
            assembly_placement=next(a.placement for a in model.assemblies if a.id == c.assembly_id),
            dependency_ids=c.dependency_ids, relationship_ids=c.relationship_ids, provenance=c.provenance))
    return Geometry(source=source, definitions=definitions, dependencies=model.dependencies, connections=model.connections)


def review_changes(before, after):
    """Conservative review, not a connection solver or clearance certification."""
    old = {d.component_id: d for d in before.definitions}
    dirty = sorted(d.component_id for d in after.definitions if digest(d) != digest(old.get(d.component_id)))
    assemblies = {d.assembly_id for d in after.definitions if d.component_id in dirty}
    issues = [{"code": "ASSEMBLY_SUPPORT_SLAB_CLEARANCE_REVIEW", "componentId": d.component_id}
              for d in after.definitions if d.assembly_id in assemblies and d.component_id not in dirty]
    issues += [{"code": "CONNECTION_REQUIRES_REVIEW", "connectionId": c.id} for c in after.connections
               if c.from_component_id in dirty or c.to_component_id in dirty]
    if dirty:
        issues.append({"code": "CLEARANCE_RULES_UNAVAILABLE", "componentIds": dirty})
    return {"changedComponentIds": dirty, "status": "REVIEW_REQUIRED" if issues else "UNCHANGED", "issues": issues}
