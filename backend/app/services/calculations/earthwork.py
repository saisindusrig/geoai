"""Preliminary earthwork formulas. All factors are editable configuration,
documented inline -- these are planning approximations, not final design.
"""

DEFAULT_BULKING_FACTOR = 1.25  # loose volume vs bank volume for ordinary soil


def rectangular_excavation_m3(length_m: float, width_m: float, depth_m: float,
                              bulking_factor: float = 1.0) -> float:
    return length_m * width_m * depth_m * bulking_factor


def trench_excavation_m3(trench_length_m: float, trench_width_m: float,
                         trench_depth_m: float, bulking_factor: float = 1.0) -> float:
    return trench_length_m * trench_width_m * trench_depth_m * bulking_factor


def pipe_backfill_m3(trench_volume_m3: float, pipe_volume_m3: float,
                     bedding_volume_m3: float) -> float:
    return max(trench_volume_m3 - pipe_volume_m3 - bedding_volume_m3, 0.0)
