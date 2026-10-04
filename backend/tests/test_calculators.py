"""Unit tests for deterministic calculators (no LLM)."""

from app.services.calculations.cost import build_line_items, cost_summary
from app.services.calculations.timeline import estimate_months
from app.services.geospatial.crs import estimate_utm_epsg


def test_cost_summary_from_line_items():
    from types import SimpleNamespace

    rates = {
        "CONC": SimpleNamespace(rate=5000.0, currency="INR"),
    }
    items = build_line_items(
        [
            {"item_code": "CONC", "item_name": "Concrete", "category": "structure", "quantity": 100, "unit": "m3", "assumption": "test"},
        ],
        rates,
    )
    summary = cost_summary(items)
    assert summary["total_medium"] > 0
    assert summary["total_low"] < summary["total_medium"]
    assert summary["total_high"] > summary["total_medium"]


def test_timeline_estimate_flyover():
    result = estimate_months("flyover", 500)
    assert result["estimated_months_medium"] > 0
    assert result["estimated_months_low"] < result["estimated_months_medium"]


def test_auto_utm_bengaluru():
    epsg = estimate_utm_epsg(77.5946, 12.9716)
    assert epsg in (32643, 32743)  # northern/southern hemisphere UTM zone 43
