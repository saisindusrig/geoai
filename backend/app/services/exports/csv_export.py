"""CSV BOQ export."""

import csv
import io

COLUMNS = ["item_code", "item_name", "category", "quantity", "unit", "rate", "amount", "assumption"]


def build_boq_csv(line_items: list[dict], disclaimer: str) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([f"# {disclaimer}"])
    writer.writerow(COLUMNS)
    for item in line_items:
        writer.writerow([item.get(col, "") for col in COLUMNS])
    return buf.getvalue().encode("utf-8-sig")
