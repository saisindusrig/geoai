"""Experimental representation translator only; production BuildingAdapter remains unchanged."""
from app.domain.ai3d import AI3DDesign
from app.services.assistant.building_specialist import BuildingAdapter


def translate_building(spec, selection_reference, source_revision=None):
    geometry=BuildingAdapter().generate(spec)
    objects=[]
    for raw in geometry["objects"]:
        semantic=raw["semantic"]
        objects.append({"objectId":semantic["sourceComponentId"],"systemId":"building-system","semanticType":semantic["componentKind"],
            "role":semantic["componentRole"],"parameters":{"primitiveType":"BOX","center":raw["center"],"size":raw["size"],"headingDeg":raw["rotation_z_deg"]}})
    return AI3DDesign(design_id=spec.building_id,source_model_revision_id=source_revision,site_selection=selection_reference,
        systems=[{"id":"building-system","assetType":"BUILDING","semanticType":"STRUCTURE","role":"BUILDING"}],objects=objects,
        input_source=spec.input_source,assumptions=spec.assumptions)
