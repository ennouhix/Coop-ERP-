"""
Génération de la facture PDF — le document commercial officiel envoyé au
client. Utilise reportlab (pur Python, aucune dépendance système), ce qui
le rend portable tel quel dans l'image Docker sans rien y ajouter.
"""
from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from apps.billing.models import Invoice
from apps.core.fields import get_translated_value


def generate_invoice_pdf(invoice: Invoice) -> BytesIO:
    """Retourne un buffer PDF prêt à être servi en téléchargement."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("InvoiceTitle", parent=styles["Title"], fontSize=20, spaceAfter=4)
    small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=9, textColor=colors.grey)

    cooperative = invoice.cooperative
    customer = invoice.customer
    elements = []

    # --- En-tête : coopérative émettrice ---
    elements.append(Paragraph(cooperative.name, title_style))
    coop_info_lines = []
    if cooperative.legal_name:
        coop_info_lines.append(cooperative.legal_name)
    if cooperative.ice:
        coop_info_lines.append(f"ICE : {cooperative.ice}")
    if cooperative.rc_number:
        coop_info_lines.append(f"RC : {cooperative.rc_number}")
    if cooperative.address:
        coop_info_lines.append(cooperative.address)
    if cooperative.phone_number:
        coop_info_lines.append(f"Tél : {cooperative.phone_number}")
    for line in coop_info_lines:
        elements.append(Paragraph(line, small_style))

    elements.append(Spacer(1, 10 * mm))

    # --- Titre facture + infos ---
    elements.append(Paragraph(f"Facture {invoice.invoice_number}", styles["Heading2"]))
    meta_table = Table(
        [
            ["Date d'émission", invoice.issue_date.strftime("%d/%m/%Y")],
            ["Date d'échéance", invoice.due_date.strftime("%d/%m/%Y")],
            ["Client", customer.name],
            ["ICE Client", customer.ice or "—"],
        ],
        colWidths=[50 * mm, 100 * mm],
    )
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8 * mm))

    # --- Lignes de facture ---
    table_data = [["Produit", "Quantité", "Prix unitaire", "Total"]]
    for line in invoice.lines.select_related("product").all():
        product_name = line.description or get_translated_value(line.product.name, "fr")
        table_data.append([
            product_name,
            f"{line.quantity} {line.product.unit.symbol}",
            f"{line.unit_price:.2f}",
            f"{line.line_total:.2f}",
        ])

    lines_table = Table(table_data, colWidths=[80 * mm, 35 * mm, 35 * mm, 30 * mm])
    lines_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d3436")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe6e9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6fa")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(lines_table)
    elements.append(Spacer(1, 6 * mm))

    # --- Totaux ---
    totals_table = Table(
        [
            ["Total", f"{invoice.total_amount:.2f}"],
            ["Payé", f"{invoice.amount_paid:.2f}"],
            ["Solde dû", f"{invoice.balance_due:.2f}"],
        ],
        colWidths=[145 * mm, 35 * mm],
    )
    totals_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("LINEABOVE", (0, 2), (-1, 2), 1, colors.black),
    ]))
    elements.append(totals_table)

    if invoice.notes:
        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph(f"Notes : {invoice.notes}", small_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
