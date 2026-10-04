"""Cost estimation from quantities x regional rates, with low/med/high range."""

from sqlalchemy.orm import Session

from app.db.models import RateItem

CONTINGENCY_PERCENT = 10.0
DESIGN_SURVEY_APPROVAL_PERCENT = 6.0  # placeholder for soft costs
RANGE_LOW_FACTOR = 0.85
RANGE_HIGH_FACTOR = 1.30


def get_rates(db: Session, region: str = "default") -> dict[str, RateItem]:
    items = db.query(RateItem).filter(RateItem.region == region).all()
    return {item.item_code: item for item in items}


def build_line_items(quantities: list[dict], rates: dict[str, RateItem]) -> list[dict]:
    """quantities: [{item_code, item_name, category, quantity, unit, assumption}]"""
    line_items = []
    for q in quantities:
        rate_item = rates.get(q["item_code"])
        rate = rate_item.rate if rate_item else 0.0
        currency = rate_item.currency if rate_item else "INR"
        line_items.append(
            {
                **q,
                "quantity": round(q["quantity"], 2),
                "rate": rate,
                "currency": currency,
                "amount": round(q["quantity"] * rate, 2),
            }
        )
    return line_items


def cost_summary(line_items: list[dict]) -> dict:
    direct = sum(li["amount"] for li in line_items)
    contingency = direct * CONTINGENCY_PERCENT / 100
    soft_costs = direct * DESIGN_SURVEY_APPROVAL_PERCENT / 100
    total = direct + contingency + soft_costs
    return {
        "direct_cost": round(direct, 2),
        "contingency_percent": CONTINGENCY_PERCENT,
        "contingency": round(contingency, 2),
        "design_survey_approval_percent": DESIGN_SURVEY_APPROVAL_PERCENT,
        "design_survey_approval": round(soft_costs, 2),
        "total_medium": round(total, 2),
        "total_low": round(total * RANGE_LOW_FACTOR, 2),
        "total_high": round(total * RANGE_HIGH_FACTOR, 2),
        "currency": line_items[0]["currency"] if line_items else "INR",
    }
