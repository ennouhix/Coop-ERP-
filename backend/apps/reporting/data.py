"""
Extraction des lignes de chaque rapport — source unique de vérité utilisée
par l'export Excel, l'export PDF et l'aperçu à l'écran (preview JSON).

Chaque fonction renvoie un couple `(en-têtes, lignes)` :
- Les montants et quantités sont des `Decimal` : numériques dans l'Excel,
  formatés en MAD dans le PDF et l'aperçu (voir `format_report_cell`).
- Les dates et statuts sont déjà au format affichable (dd/mm/YYYY, libellés
  traduits via get_*_display()).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from apps.accounting.models import AccountingEntry
from apps.billing.models import Invoice
from apps.core.fields import get_translated_value
from apps.inventory.models import StockLevel, StockMovement
from apps.members.models import Member
from apps.partners.models import Partner
from apps.purchases.models import PurchaseOrder
from apps.sales.models import SalesOrder

MONEY = "MAD"


def format_money(value: Decimal) -> str:
    """Format FR : '1 700,00 MAD' (espace milliers, virgule décimale)."""
    text = f"{value:,.2f}"
    integer_part, _, decimal_part = text.partition(".")
    return f"{integer_part.replace(',', ' ')} {decimal_part} {MONEY}"


def format_report_cell(value) -> str:  # noqa: ANN001
    """Formatage d'une cellule pour le PDF / l'aperçu (valeurs natives pour l'Excel)."""
    if isinstance(value, Decimal):
        return format_money(value)
    return "" if value is None else str(value)


# ---------------------------------------------------------------------------
# Adhérents
# ---------------------------------------------------------------------------

def members_rows(cooperative) -> tuple[list[str], list[list]]:  # noqa: ANN001
    headers = ["N° Adhérent", "Nom", "Prénom", "CIN", "Téléphone", "Statut",
           "Date d'adhésion", "Parts sociales"]
    rows = []
    members = Member.all_objects.filter(cooperative=cooperative).order_by("member_number")
    for member in members:
        rows.append([
            member.member_number,
            member.last_name,
            member.first_name,
            member.cin,
            member.phone_number,
            member.get_status_display(),
            member.join_date.strftime("%d/%m/%Y") if member.join_date else "",
            member.shares_count,
        ])
    return headers, rows


# ---------------------------------------------------------------------------
# Mouvements de stock
# ---------------------------------------------------------------------------

def stock_movements_rows(
    cooperative,
    date_from: date | None = None,
    date_to: date | None = None,
    movement_type: str | None = None,
    warehouse_id: str | None = None,
) -> tuple[list[str], list[list]]:  # noqa: ANN001
    headers = ["Date", "Type", "Raison", "Produit", "Entrepôt", "Destination",
           "Quantité", "Référence"]
    movements = StockMovement.objects.filter(cooperative=cooperative).select_related(
        "product", "warehouse", "destination_warehouse"
    )
    if date_from:
        movements = movements.filter(created_at__date__gte=date_from)
    if date_to:
        movements = movements.filter(created_at__date__lte=date_to)
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    if warehouse_id:
        movements = movements.filter(warehouse_id=warehouse_id)

    rows = []
    for movement in movements.order_by("created_at"):
        rows.append([
            movement.created_at.strftime("%d/%m/%Y %H:%M"),
            movement.get_movement_type_display(),
            movement.get_reason_display(),
            movement.product.sku,
            movement.warehouse.code,
            movement.destination_warehouse.code if movement.destination_warehouse else "",
            movement.quantity,
            movement.reference,
        ])
    return headers, rows


# ---------------------------------------------------------------------------
# Commandes de vente
# ---------------------------------------------------------------------------

def sales_orders_rows(
    cooperative,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    customer_id: str | None = None,
) -> tuple[list[str], list[list]]:  # noqa: ANN001
    headers = ["N° Commande", "Client", "Statut", "Date",
           "Montant total"]
    orders = (
    SalesOrder.objects.filter(cooperative=cooperative)
    .select_related("customer").prefetch_related("lines")
)
    if date_from:
        orders = orders.filter(order_date__gte=date_from)
    if date_to:
        orders = orders.filter(order_date__lte=date_to)
    if status:
        orders = orders.filter(status=status)
    if customer_id:
        orders = orders.filter(customer_id=customer_id)

    rows = []
    for order in orders.order_by("order_date"):
        rows.append([
            order.order_number,
            order.customer.name,
            order.get_status_display(),
            order.order_date.strftime("%d/%m/%Y"),
            order.total_amount,
        ])
    return headers, rows


# ---------------------------------------------------------------------------
# Commandes d'achat
# ---------------------------------------------------------------------------

def purchase_orders_rows(
    cooperative,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    supplier_id: str | None = None,
) -> tuple[list[str], list[list]]:  # noqa: ANN001
    headers = ["N° Commande", "Fournisseur", "Statut", "Date",
           "Montant total"]
    orders = (
    PurchaseOrder.objects.filter(cooperative=cooperative)
    .select_related("supplier").prefetch_related("lines")
)
    if date_from:
        orders = orders.filter(order_date__gte=date_from)
    if date_to:
        orders = orders.filter(order_date__lte=date_to)
    if status:
        orders = orders.filter(status=status)
    if supplier_id:
        orders = orders.filter(supplier_id=supplier_id)

    rows = []
    for order in orders.order_by("order_date"):
        rows.append([
            order.order_number,
            order.supplier.name,
            order.get_status_display(),
            order.order_date.strftime("%d/%m/%Y"),
            order.total_amount,
        ])
    return headers, rows


# ---------------------------------------------------------------------------
# Partenaires (clients / fournisseurs)
# ---------------------------------------------------------------------------

def partners_rows(
    cooperative,
    kind: str | None = None,
    status: str | None = None,
) -> tuple[list[str], list[list]]:  # noqa: ANN001
    headers = ["Code", "Nom", "Type", "ICE", "Téléphone", "Email",
           "Ville", "Statut"]
    partners = Partner.objects.filter(cooperative=cooperative)
    if kind == "customer":
        partners = partners.filter(is_customer=True)
    elif kind == "supplier":
        partners = partners.filter(is_supplier=True)
    if status:
        partners = partners.filter(status=status)

    rows = []
    for partner in partners.order_by("name"):
        roles = []
        if partner.is_customer:
            roles.append("Client")
        if partner.is_supplier:
            roles.append("Fournisseur")
        rows.append([
            partner.code,
            partner.name,
            " / ".join(roles) or "—",
            partner.ice,
            partner.phone_number,
            partner.email,
            partner.city,
            partner.get_status_display(),
        ])
    return headers, rows


# ---------------------------------------------------------------------------
# Factures
# ---------------------------------------------------------------------------

def invoices_rows(
    cooperative,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    customer_id: str | None = None,
) -> tuple[list[str], list[list]]:  # noqa: ANN001
    headers = ["N° Facture", "Client", "Statut", "Date d'émission", "Montant",
           "Payé", "Solde"]
    invoices = Invoice.objects.filter(cooperative=cooperative).select_related("customer")
    if date_from:
        invoices = invoices.filter(issue_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(issue_date__lte=date_to)
    if status:
        invoices = invoices.filter(status=status)
    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)

    rows = []
    for invoice in invoices.order_by("issue_date"):
        rows.append([
            invoice.invoice_number,
            invoice.customer.name,
            invoice.get_status_display(),
            invoice.issue_date.strftime("%d/%m/%Y"),
            invoice.total_amount,
            invoice.amount_paid,
            invoice.balance_due,
        ])
    return headers, rows


# ---------------------------------------------------------------------------
# Niveaux de stock (inventaire)
# ---------------------------------------------------------------------------

def stock_levels_rows(
    cooperative,
    warehouse_id: str | None = None,
) -> tuple[list[str], list[list]]:  # noqa: ANN001
    headers = ["Produit", "Désignation", "Entrepôt", "Quantité", "Unité"]
    levels = (
        StockLevel.objects.filter(cooperative=cooperative)
        .select_related("product", "product__unit", "warehouse")
    )
    if warehouse_id:
        levels = levels.filter(warehouse_id=warehouse_id)

    rows = []
    for level in levels.order_by("product__sku", "warehouse__code"):
        rows.append([
            level.product.sku,
            get_translated_value(level.product.name, "fr"),
            level.warehouse.code,
            level.quantity,
            level.product.unit.symbol,
        ])
    return headers, rows


# ---------------------------------------------------------------------------
# Journal comptable (une ligne par ligne d'écriture)
# ---------------------------------------------------------------------------

def accounting_journal_rows(
    cooperative,
    period: str | None = None,
    journal_id: str | None = None,
) -> tuple[list[str], list[list]]:  # noqa: ANN001
    headers = ["Date", "N° Écriture", "Journal", "Compte", "Libellé",
           "Débit", "Crédit", "Validée"]
    entries = (
    AccountingEntry.objects.filter(cooperative=cooperative)
    .select_related("journal").prefetch_related("lines__account")
)
    if period:
        entries = entries.filter(period=period)
    if journal_id:
        entries = entries.filter(journal_id=journal_id)

    rows = []
    for entry in entries.order_by("entry_date", "entry_number"):
        for line in entry.lines.all():
            rows.append([
                entry.entry_date.strftime("%d/%m/%Y"),
                entry.entry_number,
                entry.journal.code,
                (f"{line.account.code} — "
     f"{get_translated_value(line.account.name, 'fr')}"),
                line.label or entry.description,
                line.debit,
                line.credit,
                "Oui" if entry.is_posted else "Non",
            ])
    return headers, rows
