"""Pure, atomic assembly/reference checks and bounded parameter propagation.

No database writes or production proposal registration. Geometry regeneration
must consume the returned affected IDs before any future revision is persisted.
"""
from app.domain.bim import BIMProject, Parameter


def validate_foundation(project):
    spec = BIMProject.model_validate(project)
    groups = [spec.assets, spec.assemblies, spec.components, spec.materials,
              spec.cross_sections, spec.connections, spec.constraints, spec.dependencies]
    ids = [item.id for group in groups for item in group]
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_SEMANTIC_ID")
    assets = {a.id: a for a in spec.assets}
    assemblies = {a.id: a for a in spec.assemblies}
    components = {c.id: c for c in spec.components}
    materials = {m.id for m in spec.materials}
    sections = {s.id for s in spec.cross_sections}
    connections = {c.id: c for c in spec.connections}
    dependencies = {d.id: d for d in spec.dependencies}

    def unique(values):
        if len(values) != len(set(values)):
            raise ValueError("DUPLICATE_REFERENCE")

    def parameter(component_id, parameter_id):
        if component_id not in components:
            raise ValueError("UNRESOLVED_COMPONENT")
        params = {p.id: p for p in components[component_id].parameters}
        if parameter_id not in params:
            raise ValueError("UNRESOLVED_PARAMETER")
        return params[parameter_id]

    for asset in spec.assets:
        unique(asset.assembly_ids)
        if set(asset.assembly_ids) != {a.id for a in spec.assemblies if a.asset_id == asset.id}:
            raise ValueError("ASSET_MEMBERSHIP_MISMATCH")
    for assembly in spec.assemblies:
        unique(assembly.component_ids)
        if assembly.asset_id not in assets:
            raise ValueError("UNRESOLVED_ASSET")
        if set(assembly.component_ids) != {c.id for c in spec.components if c.assembly_id == assembly.id}:
            raise ValueError("ASSEMBLY_MEMBERSHIP_MISMATCH")
    for section in spec.cross_sections:
        unique([p.id for p in section.parameters])
    for component in spec.components:
        unique([p.id for p in component.parameters])
        unique(component.relationship_ids)
        unique(component.dependency_ids)
        if component.assembly_id not in assemblies or assemblies[component.assembly_id].asset_id != component.asset_id:
            raise ValueError("COMPONENT_MEMBERSHIP_MISMATCH")
        if component.material_id not in materials:
            raise ValueError("UNRESOLVED_MATERIAL")
        if component.geometry.cross_section_id is not None and component.geometry.cross_section_id not in sections:
            raise ValueError("UNRESOLVED_CROSS_SECTION")
        expected_relations = {r.id for r in spec.connections if component.id in (r.from_component_id, r.to_component_id)}
        expected_dependencies = {d.id for d in spec.dependencies if component.id in (d.source_component_id, d.target_component_id)}
        if set(component.relationship_ids) != expected_relations or set(component.dependency_ids) != expected_dependencies:
            raise ValueError("COMPONENT_REFERENCE_MISMATCH")
    for relation in connections.values():
        if relation.from_component_id not in components or relation.to_component_id not in components:
            raise ValueError("UNRESOLVED_RELATIONSHIP")
    targets = set()
    for dep in dependencies.values():
        source = parameter(dep.source_component_id, dep.source_parameter_id)
        target = parameter(dep.target_component_id, dep.target_parameter_id)
        key = (dep.target_component_id, dep.target_parameter_id)
        if key in targets:
            raise ValueError("MULTIPLE_DEPENDENCY_WRITERS")
        targets.add(key)
        if source.unit != target.unit:
            raise ValueError("DEPENDENCY_UNIT_MISMATCH")
    # Component-level ordering is conservative: no circular assembly edits.
    pending = set(components)
    order = []
    while pending:
        ready = sorted(c for c in pending if all(d.source_component_id in order for d in spec.dependencies if d.target_component_id == c))
        if not ready:
            raise ValueError("CIRCULAR_DEPENDENCY")
        order.extend(ready)
        pending.difference_update(ready)
    for constraint in spec.constraints:
        value = parameter(constraint.component_id, constraint.parameter_id).value
        if not constraint.minimum <= value <= constraint.maximum:
            raise ValueError("PARAMETER_CONSTRAINT_VIOLATION")
    return spec, order


def propagate_parameters(project, changes, *, expected_design_version):
    """Return a detached candidate and dirty IDs; never claim regenerated solids.

    COPY is explicit parameter equality only. Dependent geometry stays dirty and
    no member size or layout is inferred. Callers must bind trusted provenance.
    """
    spec, order = validate_foundation(project)
    if any(c.provenance.design_version != expected_design_version for c in spec.components):
        raise ValueError("STALE_DESIGN_VERSION")
    candidate = spec.model_dump(mode="json")
    components = {c["id"]: c for c in candidate["components"]}
    dirty_parameters = set()
    driven = {(d.target_component_id, d.target_parameter_id) for d in spec.dependencies}

    def assign(component_id, parameter_id, value):
        if component_id not in components:
            raise ValueError("UNRESOLVED_COMPONENT")
        for index, param in enumerate(components[component_id]["parameters"]):
            if param["id"] == parameter_id:
                updated = Parameter.model_validate({**param, "value": value}).model_dump()
                if updated != param:
                    components[component_id]["parameters"][index] = updated
                    dirty_parameters.add((component_id, parameter_id))
                return
        raise ValueError("UNRESOLVED_PARAMETER")

    for (component_id, parameter_id), value in changes.items():
        if (component_id, parameter_id) in driven:
            raise ValueError("DEPENDENT_PARAMETER_EDIT")
        assign(component_id, parameter_id, value)
    for component_id in order:
        for dep in spec.dependencies:
            if dep.target_component_id != component_id or (dep.source_component_id, dep.source_parameter_id) not in dirty_parameters:
                continue
            if dep.operation == "UNRESOLVED":
                raise ValueError("DEPENDENCY_REQUIRES_REVIEW")
            source = next(p for p in components[dep.source_component_id]["parameters"] if p["id"] == dep.source_parameter_id)
            assign(component_id, dep.target_parameter_id, source["value"])
    dirty = sorted({c for c, _ in dirty_parameters})
    for component_id in dirty:
        components[component_id]["validation_status"] = "UNVALIDATED"
    result, _ = validate_foundation(candidate)
    return result, dirty
