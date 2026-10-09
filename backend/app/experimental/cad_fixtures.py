"""One reusable SUPPORT_FRAME plus component proofs; no asset generators."""
from app.domain.bim import BIMProject
from app.experimental.bim_cad import CADMapping, TrustedSource

TRUSTED = TrustedSource("cad-proof", 1, None)


def params(**values):
    return [dict(id=k, value=v, unit="m") for k, v in values.items()]


def support_frame(asset_type="BRIDGE"):
    components, recipes = [], []
    def add(id, kind, operation, values, origin, section=None, horizontal=False):
        components.append(dict(id=id, asset_id="concept", assembly_id="frame", component_type=kind,
            parameters=params(**values), placement=dict(origin=origin), material_id="concrete" if kind in {"COLUMN", "SLAB"} else "steel",
            geometry=dict(primitive=dict(primitive_type="BOX", center=[0,0,0], size=[1,1,1]), cross_section_id=section),
            provenance=dict(design_id="cad-proof", design_version=1, source_kind="PREVIEW_ASSUMPTION")))
        recipes.append(dict(component_id=id, operation=operation, orientation="HORIZONTAL" if horizontal else "VERTICAL"))
    for index, origin in enumerate([(0,0,0),(5,0,0),(0,3,0),(5,3,0)]):
        add(f"column-{index}", "COLUMN", "CIRCULAR_COLUMN", dict(length=3), origin, "circle")
    for index, y in enumerate([0, 3]):
        add(f"primary-{index}", "BEAM", "PROFILE_EXTRUSION", dict(length=5), (0,y,3), "i-section", True)
    for index, y in enumerate([1,2]):
        add(f"secondary-{index}", "BEAM", "PROFILE_EXTRUSION", dict(length=5), (0,y,3), "rectangle", True)
    add("platform", "SLAB", "RECTANGULAR_OPENING", dict(width=5, depth=3, thickness=.2, hole_width=.8, hole_depth=.6), (2.5,1.5,3.25))
    add("plate", "PLATE", "CIRCULAR_HOLE", dict(width=.4, depth=.4, thickness=.02, hole_radius=.04), (0,0,3.26))
    # Only explicit length equality. No support relocation or engineering inference.
    components[4]["dependency_ids"] = ["beam-length-copy"]
    components[5]["dependency_ids"] = ["beam-length-copy"]
    model = BIMProject.model_validate(dict(assets=[dict(id="concept", asset_type=asset_type, assembly_ids=["frame"])],
        assemblies=[dict(id="frame", asset_id="concept", role="SUPPORT_FRAME", component_ids=[c["id"] for c in components])],
        components=components, materials=[dict(id="concrete",name="Concept concrete",category="CONCRETE"),dict(id="steel",name="Concept steel",category="STEEL")],
        cross_sections=[dict(id="circle",profile="CIRCLE",parameters=params(radius=.2)),
                        dict(id="rectangle",profile="RECTANGLE",parameters=params(width=.25,depth=.4)),
                        dict(id="i-section",profile="I",parameters=params(width=.3,depth=.5,web=.02,flange=.03))],
        dependencies=[dict(id="beam-length-copy",source_component_id="primary-0",source_parameter_id="length",target_component_id="primary-1",target_parameter_id="length",operation="COPY")]))
    return model, CADMapping.model_validate(dict(recipes=recipes))
