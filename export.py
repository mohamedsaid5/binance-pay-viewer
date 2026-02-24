"""PDF export helper for transaction data."""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def export_to_pdf(
    file_path: str,
    columns: list[str],
    rows: list[list[str]],
) -> None:
    """Export tabular data to a neatly formatted landscape PDF."""

    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    elements: list = []

    # ── Header ─────────────────────────────────────────────────────────────
    elements.append(
        Paragraph("Binance Pay — Transaction Report", styles["Title"])
    )
    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  &bull;  "
            f"Rows: {len(rows)}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 10))

    # ── Table ──────────────────────────────────────────────────────────────
    table_data = [columns] + rows
    table = Table(table_data, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a84ff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                # Body rows
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f5f5f5")],
                ),
            ]
        )
    )
    elements.append(table)

    # ── Page numbers ───────────────────────────────────────────────────────
    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(
            doc.pagesize[0] - 15 * mm, 10, f"Page {canvas.getPageNumber()}"
        )
        canvas.restoreState()

    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)
