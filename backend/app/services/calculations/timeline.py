"""Very rough construction duration estimate (planning only).

Productivity factors are editable placeholders, not scheduling truth.
"""

from app.core.project_catalog import project_type_family

# months per unit of work, by project type driver (base families)
DURATION_FACTORS = {
    "flyover": ("length_m", 0.018),    # ~18 months per km
    "building": ("floors", 2.5),       # ~2.5 months per floor
    "pipeline": ("pipe_length_m", 0.004),
    "road": ("length_m", 0.006),
}
MOBILIZATION_MONTHS = 1.5


def estimate_months(project_type: str, driver_value: float) -> dict:
    family = project_type_family(project_type)
    _, factor = DURATION_FACTORS.get(family, ("", 0.01))
    duration = MOBILIZATION_MONTHS + driver_value * factor
    return {
        "estimated_months_medium": round(duration, 1),
        "estimated_months_low": round(duration * 0.8, 1),
        "estimated_months_high": round(duration * 1.4, 1),
        "note": "Preliminary duration; depends on approvals, season, utilities, land availability.",
    }
