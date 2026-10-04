"""Building massing conceptual generator."""

import math

from app.services.calculations import concrete, earthwork, steel
from app.services.design.geometry_utils import box

FOUNDATION_DEPTH_M = 2.0


def generate(params: dict, design: dict) -> dict:
    geom = design.get("geometry", {})
    builtup = float(geom.get("builtup_area_sqm") or params.get("builtup_area_sqm", 400))
    floors = int(geom.get("floors") or params.get("floors", 4))
    floor_h = float(geom.get("floor_height_m") or params.get("floor_height_m", 3.2))
    slab_thk = float(params.get("slab_thickness_m", 0.15))
    grid = float(params.get("column_grid_m", 5))
    foundation_factor = float(params.get("foundation_factor", 0.3))
    grade = design.get("materials", {}).get("concrete_grade", "M25").split()[0]

    # Assume square footprint massing
    side = math.sqrt(builtup)
    cols_per_side = max(2, int(side / grid) + 1)
    column_count = cols_per_side ** 2
    beam_length = 2 * side * cols_per_side  # both directions per floor

    conc = concrete.building_concrete(
        builtup, floors, slab_thk, column_count, 0.16, floor_h,  # 0.4x0.4m columns
        beam_length, 0.3, 0.45, builtup, foundation_factor,
    )
    excavation = earthwork.rectangular_excavation_m3(side + 2, side + 2, FOUNDATION_DEPTH_M)
    steel_total = steel.steel_kg(conc["total_m3"], "building")
    cement = concrete.cement_bags(conc["total_m3"], grade)
    formwork = concrete.formwork_sqm(conc["total_m3"])

    quantities = {
        "concrete_m3": conc["total_m3"],
        "cement_bags": cement,
        "steel_kg": steel_total,
        "rebar_kg": steel_total,
        "excavation_m3": round(excavation, 1),
        "backfill_m3": round(excavation * 0.5, 1),
        "formwork_sqm": formwork,
        "asphalt_m3": 0,
        "pipe_length_m": 0,
        "pipe_diameter_mm": 0,
    }
    boq_inputs = [
        {"item_code": "EXC-SOIL", "item_name": "Foundation excavation", "category": "earthwork",
         "quantity": quantities["excavation_m3"], "unit": "m3", "assumption": f"Assumed {FOUNDATION_DEPTH_M}m foundation depth"},
        {"item_code": "CONC-M25", "item_name": f"Structural concrete {grade}", "category": "concrete",
         "quantity": conc["total_m3"], "unit": "m3", "assumption": "Slab/column/beam/foundation massing"},
        {"item_code": "STEEL-FE500", "item_name": "Reinforcement steel", "category": "steel",
         "quantity": steel_total, "unit": "kg", "assumption": "110 kg/m3 preliminary factor"},
        {"item_code": "FORMWORK", "item_name": "Formwork", "category": "concrete",
         "quantity": formwork, "unit": "sqm", "assumption": "4 sqm per m3 factor"},
    ]

    objects = [
        box("foundation", "foundation", (0, 0, -FOUNDATION_DEPTH_M / 2), (side + 1, side + 1, FOUNDATION_DEPTH_M)),
        box("excavation", "excavation", (0, 0, -FOUNDATION_DEPTH_M / 2), (side + 3, side + 3, FOUNDATION_DEPTH_M)),
    ]
    for f in range(floors):
        z0 = f * floor_h
        objects.append(box(f"slab_floor_{f+1}", "slab", (0, 0, z0 + floor_h), (side, side, slab_thk)))
        # column grid
        for i in range(cols_per_side):
            for j in range(cols_per_side):
                x = -side / 2 + i * side / max(cols_per_side - 1, 1)
                y = -side / 2 + j * side / max(cols_per_side - 1, 1)
                objects.append(box(f"col_f{f+1}_{i}_{j}", "column", (x, y, z0 + floor_h / 2), (0.4, 0.4, floor_h)))
    total_h = floors * floor_h
    objects.append(box("core", "core", (side / 4, side / 4, total_h / 2), (3.0, 5.0, total_h)))
    objects.append(box("facade", "facade", (0, 0, total_h / 2), (side + 0.2, side + 0.2, total_h)))

    return {
        "quantities": quantities,
        "boq_inputs": boq_inputs,
        "geometry_spec": {"objects": objects, "frame": "local_meters", "length_m": side},
        "timeline_driver": ("floors", floors),
        "derived": {"footprint_side_m": round(side, 1), "column_count": column_count,
                    "concrete_breakdown": conc},
    }
