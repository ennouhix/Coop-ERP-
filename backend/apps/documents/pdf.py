"""
Génération des documents commerciaux PDF du module documents (M16).

Réutilise le moteur de génération du module reporting (reportlab) et ses
helpers (pagination, format monétaire, en-tête d'identité de la coopérative).

Trois documents, rendus avec un gabarit commun :
- Bon de livraison (depuis une commande de vente, quantités livrées)
- Bon de commande fournisseur (depuis une commande d'achat)
- Bon de réception (depuis une commande d'achat, quantités reçues)

Chaque document applique, s'il existe, la personnalisation de la coopérative
`DocumentTemplate` (en-tête, pied, conditions, couleur d'accent, logo).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from apps.cooperatives.models import Cooperative
from apps.documents.models import DocumentTemplate, DocumentTemplateType
from apps.reporting.pdf import (
    _money, _NumberedCanvas, ACCENT, BORDER, GREY_TEXT, INK, LIGHT_BG, NAVY,
)


# --- Palette par défaut (cohérente avec la facture) -------------------------
DUE_COLOR = colors.HexColor("#b3261e")


@dataclass
class DocumentConfig:
    """Tout ce qui différencie un document commercial d'un autre."""

    doc_type: str
    title: str
    doc_number: str
    doc_date: date
    doc_date_label: str
    meta_lines: list[str] = field(default_factory=list)
    partner_title: str = ""
    partner_lines: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    col_widths: list[float] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    totals: list[tuple[str, str]] = field(default_factory=list)
    notes: str = ""
    signature_label: str = "Cachet et signature"
    status_label: Optional[str] = None
    status_color: Optional[colors.Color] = None


def _build_styles(accent: colors.Color):
    """Styles partagés du gabarit de document."""
    styles = getSampleStyleSheet()
    return {
        "company_name": ParagraphStyle(
            "CompanyName", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=15, leading=18, textColor=NAVY,
        ),
        "company_meta": ParagraphStyle(
            "CompanyMeta", parent=styles["Normal"], fontSize=8.5, leading=12.5, textColor=GREY_TEXT,
        ),
        "doc_title": ParagraphStyle(
            "DocTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=20, leading=23, textColor=NAVY, alignment=TA_RIGHT,
        ),
        "doc_meta_label": ParagraphStyle(
            "DocMetaLabel", parent=styles["Normal"], fontSize=8.5, leading=13,
            textColor=GREY_TEXT, alignment=TA_RIGHT,
        ),
        "status": ParagraphStyle(
            "Status", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=8.5, leading=13, textColor=GREY_TEXT, alignment=TA_RIGHT,
        ),
        "block_title": ParagraphStyle(
            "BlockTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=8, leading=11, textColor=accent, spaceAfter=4,
        ),
        "block_body": ParagraphStyle(
            "BlockBody", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=INK,
        ),
        "cell": ParagraphStyle(
            "Cell", parent=styles["Normal"], fontSize=9, leading=12.5, textColor=INK,
        ),
        "notes": ParagraphStyle(
            "Notes", parent=styles["Normal"], fontSize=8.5, leading=13, textColor=GREY_TEXT,
        ),
        "signature": ParagraphStyle(
            "Signature", parent=styles["Normal"], fontSize=8.5, leading=12,
            textColor=GREY_TEXT, alignment=TA_CENTER,
        ),
    }


def _company_header(cooperative: Cooperative, template: Optional[DocumentTemplate], styles) -> list:
    """Bloc gauche de l'en-tête : logo (optionnel), raison sociale, texte personnalisé."""
    cells: list = []
    show_logo = template.show_logo if template else True
    if show_logo:
        logo_file = getattr(cooperative, "logo", None)
        if logo_file:
            try:
                cells.append(Image(logo_file.path, width=32 * mm, height=32 * mm, kind="proportional"))
                cells.append(Spacer(1, 3 * mm))
            except Exception:
                pass
    cells.append(Paragraph(cooperative.name, styles["company_name"]))
    if cooperative.legal_name and cooperative.legal_name != cooperative.name:
        cells.append(Paragraph(cooperative.legal_name, styles["company_meta"]))
    if cooperative.address:
        cells.append(Paragraph(cooperative.address, styles["company_meta"]))
    contact_bits = [b for b in [cooperative.phone_number] if b]
    if contact_bits:
        cells.append(Paragraph(" · ".join(contact_bits), styles["company_meta"]))
    if template and template.header_text:
        cells.append(Paragraph(template.header_text, styles["company_meta"]))
    return cells


def _footer_lines(cooperative: Cooperative, template: Optional[DocumentTemplate]) -> list[str]:
    """Identifiants légaux + adresse + texte de pied personnalisé."""
    lines: list[str] = []
    legal_bits = [cooperative.name]
    if cooperative.ice:
        legal_bits.append(f"ICE {cooperative.ice}")
    if cooperative.rc_number:
        legal_bits.append(f"RC {cooperative.rc_number}")
    lines.append(" · ".join(legal_bits))
    if cooperative.address:
        lines.append(cooperative.address)
    if template and template.footer_text:
        lines.append(template.footer_text)
    return lines


def render_document(
    cooperative: Cooperative,
    cfg: DocumentConfig,
    template: Optional[DocumentTemplate] = None,
) -> BytesIO:
    """Construit le PDF d'un document commercial à partir d'un DocumentConfig."""
    accent = ACCENT
    if template and template.accent_color:
        accent = colors.HexColor(template.accent_color)
    styles = _build_styles(accent)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=28 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    elements: list = []

    # --- En-tête : identité à gauche — titre + métadonnées à droite ---------
    left_cell = _company_header(cooperative, template, styles)
    right_cell = [Paragraph(cfg.title, styles["doc_title"]), Spacer(1, 2 * mm)]
    right_cell.append(Paragraph(f"N° {cfg.doc_number}", styles["doc_meta_label"]))
    right_cell.append(
        Paragraph(f"{cfg.doc_date_label} : {cfg.doc_date.strftime('%d/%m/%Y')}", styles["doc_meta_label"])
    )
    for meta in cfg.meta_lines:
        right_cell.append(Paragraph(meta, styles["doc_meta_label"]))
    if cfg.status_label:
        right_cell.append(Spacer(1, 1.5 * mm))
        status_style = ParagraphStyle(
            "DocStatus", parent=styles["status"], textColor=cfg.status_color or DUE_COLOR,
        )
        right_cell.append(Paragraph(cfg.status_label, status_style))

    header_table = Table([[left_cell, right_cell]], colWidths=[100 * mm, 74 * mm])
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width="100%", thickness=1.2, color=NAVY))
    elements.append(Spacer(1, 7 * mm))

    # --- Partie tierce (client / fournisseur) -------------------------------
    partner_block = [
        Paragraph(cfg.partner_title, styles["block_title"]),
        Paragraph("<br/>".join(cfg.partner_lines) or "—", styles["block_body"]),
    ]
    if cfg.partner_title:
        parties_table = Table([[partner_block]], colWidths=[174 * mm])
        parties_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 9 * mm))

    # --- Tableau des lignes -------------------------------------------------
    table_data = [cfg.columns]
    for idx, row in enumerate(cfg.rows, start=1):
        designation = row[0] if row else ""
        cells = [str(idx), Paragraph(designation, styles["cell"])]
        cells.extend(row[1:])
        table_data.append(cells)

    lines_table = Table(table_data, colWidths=cfg.col_widths, repeatRows=1)
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

    # --- Totaux -------------------------------------------------------------
    if cfg.totals:
        TOTALS_BOX_PADDING = 6 * mm
        TOTALS_BOX_WIDTH = 90 * mm
        TOTALS_INNER_WIDTH = TOTALS_BOX_WIDTH - 2 * TOTALS_BOX_PADDING

        totals_inner = Table(cfg.totals, colWidths=[TOTALS_INNER_WIDTH - 40 * mm, 40 * mm])
        totals_inner.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("TEXTCOLOR", (0, 0), (0, -2), GREY_TEXT),
            ("LINEABOVE", (0, -1), (-1, -1), 0.75, NAVY),
            ("TOPPADDING", (0, -1), (-1, -1), 8),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 12),
            ("TEXTCOLOR", (1, -1), (1, -1), NAVY),
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

    # --- Signature ----------------------------------------------------------
    signature_block = [
        Spacer(1, 10 * mm),
        HRFlowable(width="60%", thickness=0.5, color=BORDER, hAlign="CENTER"),
        Spacer(1, 1.5 * mm),
        Paragraph(cfg.signature_label, styles["signature"]),
    ]
    elements.append(Table([["", signature_block]], colWidths=[100 * mm, 82 * mm],
                          style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")])))

    # --- Conditions / notes personnalisées ----------------------------------
    if cfg.notes or (template and template.terms_text):
        elements.append(Spacer(1, 8 * mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        elements.append(Spacer(1, 3 * mm))
        if cfg.notes:
            elements.append(Paragraph(f"<b>Notes :</b> {cfg.notes}", styles["notes"]))
        if template and template.terms_text:
            elements.append(Paragraph(f"<b>Conditions :</b> {template.terms_text}", styles["notes"]))

    # --- Pied de page paginé -------------------------------------------------
    footer_lines = _footer_lines(cooperative, template)
    doc.build(
        elements,
        canvasmaker=lambda *a, **kw: _NumberedCanvas(*a, footer_lines=footer_lines, **kw),
    )
    buffer.seek(0)
    return buffer


# ============================================================================
# Bons de livraison, de commande et de réception
# ============================================================================

def _product_label(line) -> str:  # noqa: ANN001
    return f"{line.product.sku} — {line.product.name.get('fr', line.product.sku)}"


GREEN_STATUS = colors.HexColor("#1c7a41")
ORANGE_STATUS = colors.HexColor("#b06a00")


def _delivery_status(order) -> tuple[str, colors.Color]:  # noqa: ANN001
    if order.is_fully_delivered:
        return "LIVRÉE", GREEN_STATUS
    if order.has_any_delivery:
        return "LIVRAISON PARTIELLE", ORANGE_STATUS
    return "EN COURS DE LIVRAISON", DUE_COLOR


def generate_delivery_note_pdf(order) -> BytesIO:  # noqa: ANN001
    """Bon de livraison d'une commande de vente (quantités livrées)."""
    total = sum((l.quantity_delivered * l.unit_price for l in order.lines.all()), Decimal("0"))
    rows = []
    for line in order.lines.select_related("product", "product__unit"):
        rows.append([
            _product_label(line),
            f"{line.quantity_ordered:g} {line.product.unit.symbol}",
            f"{line.quantity_delivered:g} {line.product.unit.symbol}",
            _money(line.unit_price),
            _money(line.quantity_delivered * line.unit_price),
        ])

    partner_lines = [f"<b>{order.customer.name}</b>"]
    if order.customer.ice:
        partner_lines.append(f"ICE : {order.customer.ice}")

    status_label, status_color = _delivery_status(order)
    cfg = DocumentConfig(
        doc_type=DocumentTemplateType.DELIVERY_NOTE,
        title="BON DE LIVRAISON",
        doc_number=order.order_number,
        doc_date=order.order_date,
        doc_date_label="Date de la commande",
        meta_lines=[f"Entrepôt : {order.warehouse.name}"],
        partner_title="LIVRÉ À",
        partner_lines=partner_lines,
        columns=["N°", "DÉSIGNATION", "QTÉ COMMANDÉE", "QTÉ LIVRÉE", "PU HT", "MONTANT HT"],
        col_widths=[10 * mm, 62 * mm, 28 * mm, 28 * mm, 23 * mm, 23 * mm],
        rows=rows,
        totals=[["Total livré", _money(total)]],
        notes=order.notes,
        signature_label="Cachet et signature du client",
        status_label=status_label,
        status_color=status_color,
    )
    return render_document(order.cooperative, cfg, _template_for(order.cooperative, cfg.doc_type))


def generate_purchase_order_pdf(order) -> BytesIO:  # noqa: ANN001
    """Bon de commande fournisseur (quantités commandées, prix convenus)."""
    rows = []
    for line in order.lines.select_related("product", "product__unit"):
        rows.append([
            _product_label(line),
            f"{line.quantity_ordered:g} {line.product.unit.symbol}",
            _money(line.unit_price),
            _money(line.line_total),
        ])

    partner_lines = [f"<b>{order.supplier.name}</b>"]
    if order.supplier.ice:
        partner_lines.append(f"ICE : {order.supplier.ice}")

    meta_lines = [f"Entrepôt de destination : {order.warehouse.name}"]
    if order.expected_delivery_date:
        meta_lines.append(f"Livraison souhaitée : {order.expected_delivery_date.strftime('%d/%m/%Y')}")

    cfg = DocumentConfig(
        doc_type=DocumentTemplateType.PURCHASE_ORDER,
        title="BON DE COMMANDE",
        doc_number=order.order_number,
        doc_date=order.order_date,
        doc_date_label="Date de la commande",
        meta_lines=meta_lines,
        partner_title="FOURNISSEUR",
        partner_lines=partner_lines,
        columns=["N°", "DÉSIGNATION", "QTÉ", "PU HT", "MONTANT HT"],
        col_widths=[10 * mm, 76 * mm, 28 * mm, 30 * mm, 30 * mm],
        rows=rows,
        totals=[["Total de la commande", _money(order.total_amount)]],
        notes=order.notes,
        signature_label="Cachet et signature du fournisseur",
        status_label="CONFIRMÉE",
        status_color=GREEN_STATUS,
    )
    return render_document(order.cooperative, cfg, _template_for(order.cooperative, cfg.doc_type))


def generate_receipt_pdf(order) -> BytesIO:  # noqa: ANN001
    """Bon de réception d'une commande d'achat (quantités reçues)."""
    total_qty = sum((line.quantity_received for line in order.lines.all()), Decimal("0"))
    rows = []
    for line in order.lines.select_related("product", "product__unit"):
        rows.append([
            _product_label(line),
            f"{line.quantity_ordered:g} {line.product.unit.symbol}",
            f"{line.quantity_received:g} {line.product.unit.symbol}",
        ])

    partner_lines = [f"<b>{order.supplier.name}</b>"]
    if order.supplier.ice:
        partner_lines.append(f"ICE : {order.supplier.ice}")

    cfg = DocumentConfig(
        doc_type=DocumentTemplateType.RECEIPT,
        title="BON DE RÉCEPTION",
        doc_number=order.order_number,
        doc_date=order.order_date,
        doc_date_label="Date de la commande",
        meta_lines=[f"Entrepôt de réception : {order.warehouse.name}"],
        partner_title="FOURNISSEUR",
        partner_lines=partner_lines,
        columns=["N°", "DÉSIGNATION", "QTÉ COMMANDÉE", "QTÉ REÇUE"],
        col_widths=[10 * mm, 88 * mm, 38 * mm, 38 * mm],
        rows=rows,
        totals=[["Quantité totale reçue", f"{total_qty:g}"]],
        notes=order.notes,
        signature_label="Cachet et signature du réceptionnaire",
        status_label="RÉCEPTIONNÉ",
        status_color=GREEN_STATUS,
    )
    return render_document(order.cooperative, cfg, _template_for(order.cooperative, cfg.doc_type))


def _template_for(cooperative: Cooperative, doc_type: str) -> Optional[DocumentTemplate]:
    """Template personnalisé de la coopérative pour ce type, ou None."""
    return DocumentTemplate.objects.filter(cooperative=cooperative, template_type=doc_type).first()
