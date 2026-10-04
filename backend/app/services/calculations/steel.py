"""Preliminary reinforcement steel estimate.

kg of steel per m3 of concrete by project type -- conventional preliminary
planning ranges, stored as editable config. NOT design values.
"""

from app.core.project_catalog import project_type_family

STEEL_KG_PER_M3 = {
    "flyover": 160.0,   # heavily reinforced bridge elements
    "building": 110.0,  # typical RCC frame building
    "pipeline": 60.0,   # chambers/encasement only
    "road": 30.0,       # minor structures, kerbs, drains
    "default": 100.0,
}


def steel_kg(concrete_m3: float, project_type: str) -> float:
    family = project_type_family(project_type)
    rate = STEEL_KG_PER_M3.get(family, STEEL_KG_PER_M3["default"])
    return round(concrete_m3 * rate)
