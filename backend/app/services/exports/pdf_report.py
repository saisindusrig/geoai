"""PDF report generation with ReportLab (all 14 sections from the spec)."""

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.disclaimer import DISCLAIMER

styles = getSampleStyleSheet()
H1 = styles["Heading1"]
H2 = styles["Heading2"]
BODY = styles["BodyText"]
WARN = ParagraphStyle("warn", parent=BODY, textColor=colors.HexColor("#8a1f1f"), fontSize=8)
NOTE = ParagraphStyle("note", parent=BODY, textColor=colors.HexColor("#555555"), fontSize=9)


def _bullets(items: list[str]) -> list:
    if not items:
        return [Paragraph("Data not available. Upload survey data or generate a design scenario first.", NOTE)]
    return [Paragraph(f"\u2022 {item}", BODY) for item in items]


def _kv_table(rows: list[tuple[str, str]]) -> Table:
    table = Table([[Paragraph(f"<b>{k}</b>", BODY), Paragraph(str(v), BODY)] for k, v in rows],
                  colWidths=[6 * cm, 10 * cm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _design_review_section(review: dict | None) -> list:
    if not review:
        return [Paragraph("Design engineering review not available — generate a design scenario first.", NOTE)]
    out: list = []
    out.append(_kv_table([
        ("Validation status", review.get("validation_status", "n/a")),
        ("Validation score", str(review.get("validation_score", "n/a"))),
        ("Geometry mode", review.get("geometry_mode", "n/a")),
        ("Elevation mode", review.get("elevation_mode", "n/a")),
        ("Planning mode", review.get("planning_mode", "n/a")),
        ("Alignment-based", "Yes" if review.get("alignment_based") else "No"),
    ]))
    warnings = review.get("warnings") or []
    if warnings:
        out.append(Spacer(1, 0.3 * cm))
        out.append(Paragraph("Design validation warnings:", BODY))
        out.extend(_bullets(warnings[:8]))
    recs = review.get("recommendations") or []
    if recs:
        out.append(Spacer(1, 0.3 * cm))
        out.append(Paragraph("Recommendations:", BODY))
        out.extend(_bullets(recs[:6]))
    out.append(Spacer(1, 0.3 * cm))
    out.append(Paragraph(review.get("conceptual_disclaimer", ""), WARN))
    return out


def _validation_section(validation: dict | None) -> list:
    if not validation:
        return [Paragraph("Validation not run.", NOTE)]
    out: list = []
    out.append(_kv_table([
        ("Accuracy tier", validation.get("accuracy_tier", "visual")),
        ("Database mode", validation.get("database_mode", "unknown")),
        ("Ready for design", "Yes" if validation.get("ready_for_design") else "No"),
        ("Ready for BOQ", "Yes" if validation.get("ready_for_boq") else "No"),
    ]))
    warnings = validation.get("warnings") or []
    if warnings:
        out.append(Spacer(1, 0.3 * cm))
        out.append(Paragraph("Validation warnings:", BODY))
        out.extend(_bullets(warnings[:8]))
    steps = validation.get("recommended_next_steps") or []
    if steps:
        out.append(Spacer(1, 0.3 * cm))
        out.append(Paragraph("Recommended next steps:", BODY))
        out.extend(_bullets(steps[:6]))
    return out


def build_pdf(project, analysis, scenario, estimate, validation: dict | None = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"sitegeoai Preliminary Plan - {project.name}")
    design = (scenario.design_output_json or {}) if scenario else {}
    calc = design.get("calculated", {})
    story = []

    # 1. Cover page
    story.append(Spacer(1, 5 * cm))
    story.append(Paragraph("sitegeoai", H1))
    story.append(Paragraph(f"Preliminary Planning Report: {project.name}", H2))
    story.append(Paragraph(f"Project type: {project.project_type.title()} | Units: {project.units}", BODY))
    story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", BODY))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(DISCLAIMER, WARN))
    story.append(PageBreak())

    # 2. Project summary
    story.append(Paragraph("2. Project Summary", H2))
    summary = design.get("summary") if scenario else None
    story.append(Paragraph(
        summary or "No design scenario generated yet. Open AI Design Studio to create a preliminary concept.",
        BODY,
    ))
    loc = project.location_name or (
        f"{project.center_lat}, {project.center_lng}" if project.center_lat is not None else "Not set"
    )
    boundary_area = validation.get("boundary_area_sqm") if validation else None
    align_len = validation.get("alignment_length_m") if validation else None
    story.append(_kv_table([
        ("Location", loc),
        ("Status", project.status),
        ("Accuracy tier", getattr(project, "accuracy_tier", None) or validation.get("accuracy_tier", "visual") if validation else "visual"),
        ("Boundary area", f"{boundary_area:,.0f} sqm" if boundary_area else "Not available"),
        ("Alignment length", f"{align_len:,.0f} m" if align_len else "Not available"),
        ("AI provider", design.get("ai_provider", "Not generated")),
    ]))

    # 3 & 4. Map / model placeholders
    story.append(Paragraph("3. Location Map", H2))
    story.append(Paragraph(
        "Interactive map available in the application. Export GeoJSON for GIS workflows.",
        BODY,
    ))
    story.append(Paragraph("4. 3D Model", H2))
    story.append(Paragraph(
        "Interactive 3D model available in the application when a design scenario has been generated.",
        BODY,
    ))

    # 5. Site analysis
    story.append(Paragraph("5. Site Analysis & Terrain", H2))
    if analysis is not None:
        story.append(_kv_table([
            ("Area", f"{analysis.area_sqm:,.0f} sqm" if analysis.area_sqm else "n/a"),
            ("Perimeter", f"{analysis.perimeter_m:,.0f} m" if analysis.perimeter_m else "n/a"),
            ("Elevation range", f"{analysis.elevation_min_m} - {analysis.elevation_max_m} m"),
            ("Slope estimate", f"{analysis.slope_percent_estimate}%"),
        ]))
    else:
        story.append(Paragraph("Site analysis not run. Run site analysis from the map or analysis page.", NOTE))

    # Validation / survey grade
    story.append(Paragraph("5b. Survey Grade & Validation", H2))
    story.extend(_validation_section(validation))

    design_review = design.get("design_review") if scenario else None
    story.append(Paragraph("5c. Design Engineering Review", H2))
    story.extend(_design_review_section(design_review))

    # 6. Assumptions
    story.append(Paragraph("6. Input Assumptions", H2))
    story.extend(_bullets(design.get("assumptions", []) if scenario else []))

    # 7 & 8. Design concept + dimensions
    story.append(Paragraph("7. Proposed Design Concept", H2))
    if scenario and design.get("layers"):
        story.extend(_bullets([f"{l['name']}: {l['description']}" for l in design.get("layers", [])]))
    else:
        story.append(Paragraph("Data not available. Generate a design scenario first.", NOTE))

    story.append(Paragraph("8. Dimensions", H2))
    geom = design.get("geometry", {}) if scenario else {}
    if geom:
        story.append(_kv_table([(k, str(v)) for k, v in geom.items()]))
    else:
        story.append(Paragraph("Data not available.", NOTE))

    # 9. BOQ
    story.append(Paragraph("9. Quantity Estimate / BOQ", H2))
    line_items = (estimate.line_items_json or []) if estimate else []
    if line_items:
        rows = [["Item", "Qty", "Unit", "Rate", "Amount"]]
        for li in line_items:
            rows.append([li["item_name"], f"{li['quantity']:,}", li["unit"],
                         f"{li['rate']:,}", f"{li['amount']:,.0f}"])
        table = Table(rows, colWidths=[7 * cm, 2.5 * cm, 1.5 * cm, 2.5 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Data not available. Generate a design scenario first.", NOTE))

    # 10. Cost estimate
    story.append(Paragraph("10. Cost Estimate", H2))
    cost = calc.get("cost_summary", {})
    if cost:
        story.append(_kv_table([
            ("Low", f"{cost.get('total_low', 0):,.0f} {cost.get('currency', '')}"),
            ("Medium", f"{cost.get('total_medium', 0):,.0f} {cost.get('currency', '')}"),
            ("High", f"{cost.get('total_high', 0):,.0f} {cost.get('currency', '')}"),
            ("Contingency", f"{cost.get('contingency_percent', 0)}%"),
        ]))
    else:
        story.append(Paragraph("Data not available. Generate a design scenario first.", NOTE))

    # 11. Construction sequence / timeline
    story.append(Paragraph("11. Construction Sequence & Timeline", H2))
    seq = design.get("construction_sequence", []) if scenario else []
    if seq:
        story.extend([Paragraph(f"{i+1}. {step}", BODY) for i, step in enumerate(seq)])
    else:
        story.append(Paragraph("Data not available.", NOTE))

    # 12. Risks
    story.append(Paragraph("12. Risk Checklist & Limitations", H2))
    story.extend(_bullets(design.get("risks", []) if scenario else []))

    # 13. Required surveys/approvals
    story.append(Paragraph("13. Required Surveys and Approvals", H2))
    story.extend(_bullets(design.get("required_permissions", []) if scenario else []))

    # 14. Disclaimer
    story.append(Paragraph("14. Engineering Disclaimer", H2))
    story.append(Paragraph(DISCLAIMER, WARN))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "This report is preliminary planning output only — not for construction approval, "
        "tender, or legal submission without licensed professional review.",
        WARN,
    ))

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(colors.HexColor("#8a1f1f"))
        canvas.drawString(1.5 * cm, 0.8 * cm, "PRELIMINARY PLANNING OUTPUT ONLY - NOT FOR CONSTRUCTION")
        canvas.drawRightString(A4[0] - 1.5 * cm, 0.8 * cm, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
