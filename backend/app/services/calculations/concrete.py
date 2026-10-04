"""Preliminary concrete volume formulas per project type.

Components are simplified massing approximations; a licensed engineer must
size all real members.
"""

# Cement bags (50kg) per m3 of concrete by grade -- preliminary nominal-mix
# figures, editable. Real values depend on the approved mix design.
CEMENT_BAGS_PER_M3 = {
    "M20": 6.5,
    "M25": 7.0,
    "M30": 7.5,
    "M35": 8.0,
    "M40": 8.5,
}

MISC_CONCRETE_FACTOR = 0.05  # 5% extra for approach slabs, wing walls, misc


def flyover_concrete(length_m: float, deck_width_m: float, deck_thickness_m: float,
                     pier_count: int, pier_cross_section_area_m2: float,
                     pier_height_m: float, pier_cap_volume_each_m3: float,
                     foundation_volume_each_m3: float) -> dict:
    deck = length_m * deck_width_m * deck_thickness_m
    piers = pier_count * pier_cross_section_area_m2 * pier_height_m
    caps = pier_count * pier_cap_volume_each_m3
    foundations = pier_count * foundation_volume_each_m3
    subtotal = deck + piers + caps + foundations
    misc = subtotal * MISC_CONCRETE_FACTOR
    return {
        "deck_m3": round(deck, 1),
        "piers_m3": round(piers, 1),
        "pier_caps_m3": round(caps, 1),
        "foundations_m3": round(foundations, 1),
        "misc_m3": round(misc, 1),
        "total_m3": round(subtotal + misc, 1),
    }


def building_concrete(builtup_area_sqm: float, floors: int, slab_thickness_m: float,
                      column_count: int, column_area_m2: float, floor_height_m: float,
                      beam_length_m: float, beam_width_m: float, beam_depth_m: float,
                      footprint_area_sqm: float, foundation_factor: float) -> dict:
    slabs = builtup_area_sqm * slab_thickness_m * floors
    columns = column_count * column_area_m2 * floor_height_m * floors
    beams = beam_length_m * beam_width_m * beam_depth_m * floors
    foundation = footprint_area_sqm * foundation_factor
    subtotal = slabs + columns + beams + foundation
    misc = subtotal * MISC_CONCRETE_FACTOR
    return {
        "slabs_m3": round(slabs, 1),
        "columns_m3": round(columns, 1),
        "beams_m3": round(beams, 1),
        "foundation_m3": round(foundation, 1),
        "misc_m3": round(misc, 1),
        "total_m3": round(subtotal + misc, 1),
    }


def cement_bags(concrete_m3: float, grade: str = "M25") -> float:
    bags_per_m3 = CEMENT_BAGS_PER_M3.get(grade.upper(), 7.0)
    return round(concrete_m3 * bags_per_m3)


def formwork_sqm(concrete_m3: float, factor_sqm_per_m3: float = 4.0) -> float:
    """Rough contact-area factor (editable); typical RCC 3-6 sqm per m3."""
    return round(concrete_m3 * factor_sqm_per_m3, 1)
