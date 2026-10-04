"""Pipeline / drainage trench conceptual generator."""

import math

from app.services.calculations import earthwork
from app.services.design.geometry_utils import box, cylinder


def generate(params: dict, design: dict) -> dict:
    geom = design.get("geometry", {})
    length = float(geom.get("length_m") or params.get("length_m", 300))
    dia_mm = float(geom.get("pipe_diameter_mm") or params.get("pipe_diameter_mm", 600))
    trench_w = float(params.get("trench_width_m", max(1.2, dia_mm / 1000 + 0.6)))
    trench_d = float(params.get("trench_depth_m", 2.0))
    bedding_thk = float(params.get("bedding_thickness_m", 0.15))
    manhole_spacing = float(params.get("manhole_spacing_m", 30))
    utility = params.get("utility_type", "drainage")  # drainage|water

    dia_m = dia_mm / 1000
    trench_vol = earthwork.trench_excavation_m3(length, trench_w, trench_d)
    pipe_vol = math.pi * (dia_m / 2) ** 2 * length
    bedding_vol = length * trench_w * bedding_thk
    backfill = earthwork.pipe_backfill_m3(trench_vol, pipe_vol, bedding_vol)
    manhole_count = max(2, int(length / manhole_spacing) + 1)

    pipe_code = "PIPE-RCC-600" if utility == "drainage" else "PIPE-HDPE-300"
    quantities = {
        "concrete_m3": round(manhole_count * 1.8, 1),  # ~1.8 m3 per manhole
        "cement_bags": round(manhole_count * 1.8 * 7.0),
        "steel_kg": round(manhole_count * 1.8 * 60),
        "rebar_kg": round(manhole_count * 1.8 * 60),
        "excavation_m3": round(trench_vol, 1),
        "backfill_m3": round(backfill, 1),
        "formwork_sqm": round(manhole_count * 6.0, 1),
        "asphalt_m3": 0,
        "pipe_length_m": round(length, 1),
        "pipe_diameter_mm": dia_mm,
    }
    boq_inputs = [
        {"item_code": "EXC-SOIL", "item_name": "Trench excavation", "category": "earthwork",
         "quantity": quantities["excavation_m3"], "unit": "m3", "assumption": f"{trench_w}m wide x {trench_d}m deep trench"},
        {"item_code": "BEDDING-SAND", "item_name": "Sand bedding", "category": "earthwork",
         "quantity": round(bedding_vol, 1), "unit": "m3", "assumption": f"{int(bedding_thk*1000)}mm bedding layer"},
        {"item_code": pipe_code, "item_name": f"{utility.title()} pipe {int(dia_mm)}mm", "category": "pipeline",
         "quantity": round(length, 1), "unit": "m", "assumption": "Material per utility type"},
        {"item_code": "BACKFILL", "item_name": "Backfill with compaction", "category": "earthwork",
         "quantity": quantities["backfill_m3"], "unit": "m3", "assumption": "Trench minus pipe and bedding"},
        {"item_code": "CONC-M25", "item_name": f"Manhole concrete ({manhole_count} nos)", "category": "concrete",
         "quantity": quantities["concrete_m3"], "unit": "m3", "assumption": f"Manholes every {int(manhole_spacing)}m"},
    ]

    pipe_layer = "pipe_drain" if utility == "drainage" else "pipe_water"
    pipe_z = -trench_d + bedding_thk + dia_m / 2
    objects = [
        box("trench_cut", "excavation", (0, 0, -trench_d / 2), (length, trench_w, trench_d)),
        box("bedding", "bedding", (0, 0, -trench_d + bedding_thk / 2), (length, trench_w, bedding_thk)),
        cylinder("pipe", pipe_layer, (-length / 2, 0, pipe_z), (length / 2, 0, pipe_z), dia_m / 2),
        box("backfill", "backfill", (0, 0, (-trench_d + bedding_thk + dia_m) / 2 + 0.01),
            (length, trench_w, max(trench_d - bedding_thk - dia_m, 0.1))),
    ]
    for i in range(manhole_count):
        x = -length / 2 + i * (length / max(manhole_count - 1, 1))
        objects.append(box(f"manhole_{i+1}", "manhole", (x, 0, -trench_d / 2), (1.2, 1.2, trench_d + 0.3)))

    return {
        "quantities": quantities,
        "boq_inputs": boq_inputs,
        "geometry_spec": {"objects": objects, "frame": "local_meters", "length_m": length},
        "timeline_driver": ("pipe_length_m", length),
        "derived": {"manhole_count": manhole_count, "trench_volume_m3": round(trench_vol, 1)},
    }
