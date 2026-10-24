"""CSV BOQ export."""

import csv
import io

COLUMNS = ["item_code", "item_name", "category", "quantity", "unit", "rate", "amount", "assumption"]


def _cell(value):
    # CSV quoting alone does not stop spreadsheet formula evaluation.
    # Numeric engineering values keep their type and exact value.
    if isinstance(value, str) and (value.lstrip().startswith(('=', '+', '-', '@'))
                                   or value.startswith(('\t', '\r', '\n', '\x00'))):
        return "'" + value
    return value


def build_boq_csv(line_items: list[dict], disclaimer: str) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([f"# {disclaimer}"])
    writer.writerow(COLUMNS)
    for item in line_items:
        writer.writerow([_cell(item.get(col, "")) for col in COLUMNS])
    return buf.getvalue().encode("utf-8-sig")
