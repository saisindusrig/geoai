"""Generation job telemetry summaries."""

from __future__ import annotations

from typing import Any


def build_generation_diagnostics(
    timings_ms: dict[str, float] | None,
    *,
    mode: str,
    provider: str,
    duration_ms: int | None = None,
    error_type: str | None = None,
    failed_stage: str | None = None,
    cancel_requested: bool = False,
) -> dict[str, Any]:
    timings = timings_ms or {}
    computed_total = round(sum(timings.values()), 1) if timings else None
    return {
        "total_duration_ms": duration_ms if duration_ms is not None else computed_total,
        "llm_planning_ms": timings.get("llm_planning"),
        "elevation_sampling_ms": timings.get("terrain_elevation"),
        "site_geometry_ms": timings.get("site_geometry"),
        "geometry_3d_ms": timings.get("geometry_3d"),
        "glb_preview_ms": timings.get("glb_preview"),
        "glb_final_ms": timings.get("glb_export"),
        "boq_ms": timings.get("boq_calculation"),
        "validation_ms": timings.get("validation"),
        "file_save_ms": timings.get("database_save"),
        "provider": provider,
        "generation_mode": mode,
        "failure_reason": error_type,
        "failed_stage": failed_stage,
        "cancelled": cancel_requested,
        "timings_ms": timings,
    }
