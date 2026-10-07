"""Build editable architectural and structural geometry from an approved specification."""
import math

from app.services.ai.building_plan import BuildingSpec
from app.services.design.geometry_utils import box


def generate(raw):
    spec = BuildingSpec.model_validate(raw)
    objects = []

    def solid(name, layer, center, size, rotation=0):
        if min(size) > 0.0001:
            objects.append(box(name, layer, center, size, rotation))

    def along(name, layer, start, end, offset, length, width, z, height):
        total = math.dist(start, end)
        ux, uy = (end[0]-start[0])/total, (end[1]-start[1])/total
        solid(name, layer, (start[0]+ux*(offset+length/2), start[1]+uy*(offset+length/2), z+height/2),
              (length, width, height), math.degrees(math.atan2(uy, ux)))

    fp = spec.footprint
    for floor in range(spec.floors + 1):
        solid(f"slab-{floor}", "slab", (fp.x+fp.width/2, fp.y+fp.depth/2, floor*spec.floor_height-spec.slab_thickness/2),
              (fp.width, fp.depth, spec.slab_thickness))
    for index, col in enumerate(spec.columns):
        solid(f"foundation-{index}", "foundation", (col.x, col.y, -spec.foundation_depth/2-spec.slab_thickness),
              (spec.foundation_width, spec.foundation_width, spec.foundation_depth))
        for floor in range(spec.floors):
            solid(f"column-{index}-floor-{floor}", "column", (col.x, col.y, floor*spec.floor_height+spec.floor_height/2),
                  (col.size, col.size, spec.floor_height))
    for index, beam in enumerate(spec.beams):
        for floor in range(spec.floors):
            along(f"beam-{index}-floor-{floor}", "beam", beam.start, beam.end, 0, math.dist(beam.start, beam.end),
                  beam.width, (floor+1)*spec.floor_height-spec.slab_thickness-beam.depth, beam.depth)
    for room in spec.rooms:
        solid(f"room-{room.id}-{room.name}", "room", (room.x+room.width/2, room.y+room.depth/2, room.floor*spec.floor_height+0.01),
              (room.width, room.depth, 0.02))
    for wall in spec.walls:
        base = wall.floor * spec.floor_height
        height = spec.floor_height - spec.slab_thickness
        length = math.dist(wall.start, wall.end)
        cursor = 0
        openings = sorted((o for o in spec.openings if o.wall_id == wall.id), key=lambda o: o.offset)
        for opening in openings:
            along(f"wall-{wall.id}-before-{opening.id}", "wall", wall.start, wall.end, cursor, opening.offset-cursor,
                  wall.thickness, base, height)
            along(f"wall-{wall.id}-sill-{opening.id}", "wall", wall.start, wall.end, opening.offset, opening.width,
                  wall.thickness, base, opening.sill)
            along(f"wall-{wall.id}-lintel-{opening.id}", "wall", wall.start, wall.end, opening.offset, opening.width,
                  wall.thickness, base+opening.sill+opening.height, height-opening.sill-opening.height)
            along(opening.id, opening.kind, wall.start, wall.end, opening.offset, opening.width,
                  0.04, base+opening.sill, opening.height)
            cursor = opening.offset + opening.width
        along(f"wall-{wall.id}-end", "wall", wall.start, wall.end, cursor, length-cursor, wall.thickness, base, height)

    concrete = sum(math.prod(obj["size"]) for obj in objects if obj["layer"] in {"column", "beam", "slab", "foundation"})
    quantities = {"concrete_m3": round(concrete, 3), "cement_bags": round(concrete*7.2, 1),
                  "steel_kg": round(concrete*110, 1), "rebar_kg": round(concrete*110, 1),
                  "excavation_m3": 0, "backfill_m3": 0, "formwork_sqm": 0,
                  "asphalt_m3": 0, "pipe_length_m": 0, "pipe_diameter_mm": 0}
    return {"geometry_spec": {"objects": objects, "frame": "local_meters", "length_m": fp.width,
                               "building_spec": spec.model_dump()}, "quantities": quantities,
            "boq_inputs": [{"item_code": "CONC-M25", "item_name": "Concept structural concrete", "category": "concrete",
                            "quantity": quantities["concrete_m3"], "unit": "m3", "assumption": "Concept member volumes; not engineered quantities"}],
            "timeline_driver": ("floors", spec.floors),
            "derived": {"footprint_area_sqm": fp.width*fp.depth, "column_count": len(spec.columns)}}
