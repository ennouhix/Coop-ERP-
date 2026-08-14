"""
Génération de la facture PDF — le document commercial officiel envoyé au
client. Utilise reportlab (pur Python, aucune dépendance système), ce qui
le rend portable tel quel dans l'image Docker sans rien y ajouter.

Design "grande entreprise" : en-tête avec logo, bloc TVA détaillé,
coordonnées bancaires, mentions légales obligatoires, zone cachet/signature,
pied de page paginé.

Certains éléments (TVA, IBAN, IF, patente, CNSS, remise par ligne, logo,
conditions de paiement) sont optionnels : le PDF s'adapte automatiquement
selon que ces champs existent ou non sur vos modèles Invoice / Cooperative /
InvoiceLine, via getattr(..., None). Ajoutez ces champs à vos modèles pour
que les sections correspondantes apparaissent.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from apps.billing.models import Invoice
from apps.core.fields import get_translated_value
from apps.reporting import data as report_data

# --- Palette (sobre, corporate) --------------------------------------------
NAVY = colors.HexColor("#122036")
INK = colors.HexColor("#1f2937")
ACCENT = colors.HexColor("#2e6ff2")
GREY_TEXT = colors.HexColor("#6b7280")
LIGHT_BG = colors.HexColor("#f4f6fb")
BORDER = colors.HexColor("#d7dce6")
DUE_RED = colors.HexColor("#b3261e")
PAID_GREEN = colors.HexColor("#1c7a41")

CURRENCY = "MAD"
VAT_RATE_DEFAULT = Decimal("20")  # taux TVA standard au Maroc, utilisé seulement en fallback


def _money(value) -> str:
    """Format corporate FR : '1 700,00 MAD' (espace milliers, virgule décimale)."""
    if value is None:
        value = Decimal("0")
    text = f"{value:,.2f}"
    integer_part, _, decimal_part = text.partition(".")
    integer_part = integer_part.replace(",", " ")
    return f"{integer_part},{decimal_part} {CURRENCY}"


def _first_present(obj, *names):
    """Renvoie la première valeur non nulle parmi plusieurs noms d'attributs possibles."""
    for name in names:
        value = getattr(obj, name, None)
        if value:
            return value
    return None


class _NumberedCanvas(pdf_canvas.Canvas):
    """Canvas qui ajoute 'Page X / Y' + mentions légales une fois le total de pages connu."""

    def __init__(self, *args, footer_lines=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []
        self._footer_lines = footer_lines or []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            self._draw_footer(total_pages)
            super().showPage()
        super().save()

    def _draw_footer(self, total_pages):
        width, _ = A4
        top_y = 20 * mm

        self.setStrokeColor(BORDER)
        self.setLineWidth(0.5)
        self.line(20 * mm, top_y, width - 20 * mm, top_y)

        y = top_y - 5 * mm
        self.setFont("Helvetica", 7.5)
        self.setFillColor(GREY_TEXT)
        for line in self._footer_lines:
            self.drawCentredString(width / 2, y, line)
            y -= 3.6 * mm

        self.setFont("Helvetica", 8)
        self.drawRightString(width - 20 * mm, top_y - 5 * mm, f"Page {self._pageNumber} / {total_pages}")


def generate_invoice_pdf(invoice: Invoice) -> BytesIO:
    """Retourne un buffer PDF prêt à être servi en téléchargement."""
    buffer = BytesIO()

    cooperative = invoice.cooperative
    customer = invoice.customer

    # --- Champs optionnels, activés uniquement s'ils existent sur vos modèles ---
    logo_path = _first_present(cooperative, "logo_path")
    logo_file = getattr(cooperative, "logo", None)  # ex: ImageField -> .path
    if logo_file and not logo_path:
        logo_path = getattr(logo_file, "path", None)

    tax_identifier = _first_present(cooperative, "tax_identifier", "if_number", "identifiant_fiscal")
    patente = _first_present(cooperative, "patente_number", "patente")
    cnss = _first_present(cooperative, "cnss_number", "cnss")
    bank_name = _first_present(cooperative, "bank_name")
    bank_iban = _first_present(cooperative, "iban", "rib")
    bank_swift = _first_present(cooperative, "swift", "bic")
    payment_terms = _first_present(invoice, "payment_terms", "payment_method_label")
    if not payment_terms:
        payment_terms = _first_present(cooperative, "default_payment_terms")

    subtotal = getattr(invoice, "subtotal", None) or getattr(invoice, "total_ht", None)
    tax_amount = getattr(invoice, "tax_amount", None)
    tax_rate = getattr(invoice, "tax_rate", None)
    total_ttc = getattr(invoice, "total_ttc", None) or invoice.total_amount

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=28 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    style_company_name = ParagraphStyle(
        "CompanyName", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=15, leading=18, textColor=NAVY,
    )
    style_company_meta = ParagraphStyle(
        "CompanyMeta", parent=styles["Normal"], fontSize=8.5, leading=12.5, textColor=GREY_TEXT,
    )
    style_doc_title = ParagraphStyle(
        "DocTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=20, leading=23, textColor=NAVY, alignment=TA_RIGHT,
    )
    style_doc_meta_label = ParagraphStyle(
        "DocMetaLabel", parent=styles["Normal"], fontSize=8.5, leading=13,
        textColor=GREY_TEXT, alignment=TA_RIGHT,
    )
    style_block_title = ParagraphStyle(
        "BlockTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=8, leading=11, textColor=ACCENT, spaceAfter=4,
    )
    style_block_body = ParagraphStyle(
        "BlockBody", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=INK,
    )
    style_cell = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=9, leading=12.5, textColor=INK)
    style_notes = ParagraphStyle("Notes", parent=styles["Normal"], fontSize=8.5, leading=13, textColor=GREY_TEXT)
    style_bank_title = ParagraphStyle(
        "BankTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=8, leading=11, textColor=NAVY,
    )
    style_signature = ParagraphStyle(
        "Signature", parent=styles["Normal"], fontSize=8.5, leading=12,
        textColor=GREY_TEXT, alignment=TA_CENTER,
    )

    elements = []

    # ======================================================================
    # EN-TÊTE : logo / identité à gauche — "FACTURE" + métadonnées à droite
    # ======================================================================
    left_cell = []
    if logo_path:
        try:
            left_cell.append(Image(logo_path, width=32 * mm, height=32 * mm, kind="proportional"))
            left_cell.append(Spacer(1, 3 * mm))
        except Exception:
            pass
    left_cell.append(Paragraph(cooperative.name, style_company_name))
    if cooperative.legal_name and cooperative.legal_name != cooperative.name:
        left_cell.append(Paragraph(cooperative.legal_name, style_company_meta))
    if cooperative.address:
        left_cell.append(Paragraph(cooperative.address, style_company_meta))
    contact_bits = [b for b in [cooperative.phone_number] if b]
    if contact_bits:
        left_cell.append(Paragraph(" · ".join(contact_bits), style_company_meta))

    balance_due = invoice.balance_due
    status_label = "PAYÉE" if balance_due <= 0 else "EN ATTENTE DE RÈGLEMENT"
    status_color = PAID_GREEN if balance_due <= 0 else colors.HexColor("#b06a00")
    style_status = ParagraphStyle(
        "Status", parent=style_doc_meta_label, fontName="Helvetica-Bold", textColor=status_color,
    )

    right_cell = [
        Paragraph("FACTURE", style_doc_title),
        Spacer(1, 2 * mm),
        Paragraph(f"N° {invoice.invoice_number}", style_doc_meta_label),
        Paragraph(f"Date d'émission : {invoice.issue_date.strftime('%d/%m/%Y')}", style_doc_meta_label),
        Paragraph(f"Date d'échéance : {invoice.due_date.strftime('%d/%m/%Y')}", style_doc_meta_label),
        Spacer(1, 1.5 * mm),
        Paragraph(status_label, style_status),
    ]

    header_table = Table([[left_cell, right_cell]], colWidths=[100 * mm, 74 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width="100%", thickness=1.2, color=NAVY))
    elements.append(Spacer(1, 7 * mm))

    # ======================================================================
    # IDENTIFIANTS LÉGAUX ÉMETTEUR + BLOC CLIENT
    # ======================================================================
    issuer_id_lines = []
    if cooperative.ice:
        issuer_id_lines.append(f"ICE : {cooperative.ice}")
    if cooperative.rc_number:
        issuer_id_lines.append(f"RC : {cooperative.rc_number}")
    if tax_identifier:
        issuer_id_lines.append(f"IF : {tax_identifier}")
    if patente:
        issuer_id_lines.append(f"Patente : {patente}")
    if cnss:
        issuer_id_lines.append(f"CNSS : {cnss}")

    customer_lines = [f"<b>{customer.name}</b>"]
    if customer.ice:
        customer_lines.append(f"ICE : {customer.ice}")

    issuer_block = [
        Paragraph("IDENTIFIANTS ÉMETTEUR", style_block_title),
        Paragraph("<br/>".join(issuer_id_lines) or "—", style_block_body),
    ]
    customer_block = [
        Paragraph("FACTURÉ À", style_block_title),
        Paragraph("<br/>".join(customer_lines), style_block_body),
    ]
    conditions_lines = []
    if payment_terms:
        conditions_lines.append(str(payment_terms))
    conditions_lines.append(f"Échéance : {invoice.due_date.strftime('%d/%m/%Y')}")
    conditions_block = [
        Paragraph("CONDITIONS", style_block_title),
        Paragraph("<br/>".join(conditions_lines), style_block_body),
    ]

    parties_table = Table(
        [[issuer_block, customer_block, conditions_block]],
        colWidths=[58 * mm, 58 * mm, 58 * mm],
    )
    parties_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (0, 0), 0.5, BORDER),
        ("BOX", (1, 0), (1, 0), 0.5, BORDER),
        ("BOX", (2, 0), (2, 0), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    elements.append(parties_table)
    elements.append(Spacer(1, 9 * mm))

    # ======================================================================
    # LIGNES DE FACTURE (numérotées, avec remise si présente sur la ligne)
    # ======================================================================
    has_discount = any(getattr(l, "discount_percent", None) for l in invoice.lines.all())

    header_row = ["N°", "DÉSIGNATION", "QTÉ", "PU HT"]
    if has_discount:
        header_row.append("REMISE")
    header_row.append("MONTANT HT")
    table_data = [header_row]

    col_widths = [10 * mm, 68 * mm, 24 * mm, 28 * mm]
    if has_discount:
        col_widths.append(18 * mm)
    col_widths.append(26 * mm)

    for idx, line in enumerate(invoice.lines.select_related("product").all(), start=1):
        product_name = line.description or get_translated_value(line.product.name, "fr")
        row = [
            str(idx),
            Paragraph(product_name, style_cell),
            f"{line.quantity} {line.product.unit.symbol}",
            _money(line.unit_price),
        ]
        if has_discount:
            discount = getattr(line, "discount_percent", None)
            row.append(f"{discount:g} %" if discount else "—")
        row.append(_money(line.line_total))
        table_data.append(row)

    lines_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    align_from_col = 2
    lines_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (align_from_col, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(lines_table)
    elements.append(Spacer(1, 7 * mm))

    # ======================================================================
    # TOTAUX : détail TVA si le modèle l'expose, sinon total simple
    # ======================================================================
    total_rows = []
    if subtotal is not None and (tax_amount is not None or tax_rate is not None):
        rate_label = f"TVA ({tax_rate:g}%)" if tax_rate is not None else "TVA"
        total_rows.append(["Total HT", _money(subtotal)])
        total_rows.append([rate_label, _money(tax_amount)])
        total_rows.append(["Total TTC", _money(total_ttc)])
    else:
        total_rows.append(["Total", _money(invoice.total_amount)])

    total_rows.append(["Payé", _money(invoice.amount_paid)])

    # Largeur de contenu disponible = A4 (210mm) - marges gauche/droite (18mm x2) = 174mm.
    # La table imbriquée doit tenir dans : largeur de sa cellule - padding gauche/droite.
    TOTALS_BOX_PADDING = 6 * mm
    TOTALS_BOX_WIDTH = 90 * mm  # cellule grisée (colonne 2 de totals_wrapper)
    TOTALS_INNER_WIDTH = TOTALS_BOX_WIDTH - 2 * TOTALS_BOX_PADDING  # = 78mm

    balance_color = DUE_RED if balance_due > 0 else PAID_GREEN
    totals_inner = Table(
        total_rows + [["Net à payer", _money(balance_due)]],
        colWidths=[TOTALS_INNER_WIDTH - 40 * mm, 40 * mm],
    )
    totals_inner.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TEXTCOLOR", (0, 0), (0, -2), GREY_TEXT),
        ("LINEABOVE", (0, -1), (-1, -1), 0.75, NAVY),
        ("TOPPADDING", (0, -1), (-1, -1), 8),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("TEXTCOLOR", (1, -1), (1, -1), balance_color),
        ("TEXTCOLOR", (0, -1), (0, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -2), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    totals_wrapper = Table(
        [["", totals_inner]],
        colWidths=[174 * mm - TOTALS_BOX_WIDTH, TOTALS_BOX_WIDTH],
    )
    totals_wrapper.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (1, 0), (1, 0), 0.5, BORDER),
        ("BACKGROUND", (1, 0), (1, 0), LIGHT_BG),
        ("LEFTPADDING", (1, 0), (1, 0), TOTALS_BOX_PADDING),
        ("RIGHTPADDING", (1, 0), (1, 0), TOTALS_BOX_PADDING),
        ("TOPPADDING", (1, 0), (1, 0), 8),
        ("BOTTOMPADDING", (1, 0), (1, 0), 8),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
    ]))
    elements.append(totals_wrapper)
    elements.append(Spacer(1, 10 * mm))

    # ======================================================================
    # COORDONNÉES BANCAIRES + CACHET / SIGNATURE
    # ======================================================================
    bank_block = []
    if bank_iban or bank_name:
        bank_lines = []
        if bank_name:
            bank_lines.append(f"Banque : {bank_name}")
        if bank_iban:
            bank_lines.append(f"IBAN : {bank_iban}")
        if bank_swift:
            bank_lines.append(f"SWIFT/BIC : {bank_swift}")
        bank_block = [
            Paragraph("COORDONNÉES BANCAIRES", style_bank_title),
            Spacer(1, 1.5 * mm),
            Paragraph("<br/>".join(bank_lines), style_block_body),
        ]

    signature_block = [
        Spacer(1, 10 * mm),
        HRFlowable(width="60%", thickness=0.5, color=BORDER, hAlign="CENTER"),
        Spacer(1, 1.5 * mm),
        Paragraph("Cachet et signature", style_signature),
    ]

    if bank_block:
        bottom_table = Table([[bank_block, signature_block]], colWidths=[100 * mm, 82 * mm])
        bottom_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elements.append(bottom_table)
    else:
        bottom_table = Table([["", signature_block]], colWidths=[100 * mm, 82 * mm])
        bottom_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elements.append(bottom_table)

    if invoice.notes:
        elements.append(Spacer(1, 8 * mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(f"<b>Notes :</b> {invoice.notes}", style_notes))

    # --- Mention légale de pénalités de retard (obligatoire au Maroc) -------
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(
        "Conformément à la réglementation en vigueur, tout retard de paiement au-delà de la date "
        "d'échéance pourra donner lieu à des pénalités de retard.",
        style_notes,
    ))

    # ======================================================================
    # PIED DE PAGE : identifiants légaux complets + pagination
    # ======================================================================
    legal_bits = [cooperative.name]
    if cooperative.ice:
        legal_bits.append(f"ICE {cooperative.ice}")
    if cooperative.rc_number:
        legal_bits.append(f"RC {cooperative.rc_number}")
    if tax_identifier:
        legal_bits.append(f"IF {tax_identifier}")
    if patente:
        legal_bits.append(f"Patente {patente}")
    if cnss:
        legal_bits.append(f"CNSS {cnss}")
    footer_line1 = " · ".join(legal_bits)
    footer_lines = [footer_line1]
    if cooperative.address:
        footer_lines.append(cooperative.address)

    doc.build(
        elements,
        canvasmaker=lambda *a, **kw: _NumberedCanvas(*a, footer_lines=footer_lines, **kw),
    )
    buffer.seek(0)
    return buffer

def generate_report_pdf(
    cooperative,
    title: str,
    subtitle: str,
    headers: list,
    rows: list,
) -> BytesIO:
    """Rapport tabulaire générique (membres, stock, ventes, etc.), paginé."""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=14 * mm, bottomMargin=20 * mm, leftMargin=14 * mm, rightMargin=14 * mm,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "ReportTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=15, leading=18, textColor=NAVY,
    )
    style_coop = ParagraphStyle(
        "ReportCoop", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=9, leading=12, textColor=GREY_TEXT,
    )
    style_subtitle = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"], fontSize=8, leading=11, textColor=GREY_TEXT,
    )
    style_cell = ParagraphStyle(
        "ReportCell", parent=styles["Normal"], fontSize=7.8, leading=10.5, textColor=INK,
    )
    style_head = ParagraphStyle(
        "ReportHead", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=7.8, leading=10, textColor=colors.white,
    )

    legal_bits = [cooperative.name]
    if cooperative.ice:
        legal_bits.append(f"ICE {cooperative.ice}")
    if cooperative.rc_number:
        legal_bits.append(f"RC {cooperative.rc_number}")
    footer_lines = [" · ".join(legal_bits)]
    if cooperative.address:
        footer_lines.append(cooperative.address)

    elements = []
    header_table = Table(
        [[Paragraph(cooperative.name, style_coop), Paragraph(title, style_title)]],
        colWidths=[100 * mm, 82 * mm],
    )
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(header_table)
    elements.append(Spacer(1, 1.5 * mm))
    subtitle_line = "Généré le " + date.today().strftime("%d/%m/%Y")
    if subtitle:
        subtitle_line += " · " + subtitle
    elements.append(Paragraph(subtitle_line, style_subtitle))
    elements.append(Spacer(1, 2.5 * mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    elements.append(Spacer(1, 5 * mm))

    if not rows:
        elements.append(Paragraph("Aucune donnée à afficher.", style_cell))
    else:
        table_data = [[Paragraph(h, style_head) for h in headers]]
        table_data += [
            [Paragraph(report_data.format_report_cell(value), style_cell) for value in row]
            for row in rows
        ]
        report_table = Table(table_data, repeatRows=1)
        report_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(report_table)

    doc.build(
        elements,
        canvasmaker=lambda *a, **kw: _NumberedCanvas(*a, footer_lines=footer_lines, **kw),
    )
    buffer.seek(0)
    return buffer
