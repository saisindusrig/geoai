"""Bill of Quantities assembly: generator outputs x rate table -> line items."""

from sqlalchemy.orm import Session

from app.services.calculations import cost


def build_boq(db: Session, boq_inputs: list[dict], region: str = "default") -> dict:
    rates = cost.get_rates(db, region)
    line_items = cost.build_line_items(boq_inputs, rates)
    summary = cost.cost_summary(line_items)
    return {"line_items": line_items, "cost_summary": summary}
