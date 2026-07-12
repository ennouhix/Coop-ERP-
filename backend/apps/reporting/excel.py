"""
Exports Excel — un patron simple réutilisable : en-têtes stylés, largeurs
de colonnes ajustées, une feuille par export. Représentatif de trois
modules différents (Membres, Stock, Ventes) ; le même patron s'applique
telle quelle à n'importe quel autre listing.
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.cooperatives.models import Cooperative
from apps.inventory.models import StockMovement
from apps.members.models import Member
from apps.sales.models import SalesOrder

HEADER_FILL = PatternFill(start_color="2D3436", end_color="2D3436", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def _write_header(ws, headers: list) -> None:  # noqa: ANN001
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        ws.column_dimensions[get_column_letter(col_idx)].width = max(len(header) + 4, 14)


def _to_buffer(workbook: Workbook) -> BytesIO:
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def export_members_excel(cooperative: Cooperative) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Membres"
    _write_header(ws, ["N° Adhérent", "Nom", "Prénom", "CIN", "Téléphone", "Statut", "Date d'adhésion", "Parts sociales"])

    members = Member.all_objects.filter(cooperative=cooperative).order_by("member_number")
    for row_idx, member in enumerate(members, start=2):
        ws.cell(row=row_idx, column=1, value=member.member_number)
        ws.cell(row=row_idx, column=2, value=member.last_name)
        ws.cell(row=row_idx, column=3, value=member.first_name)
        ws.cell(row=row_idx, column=4, value=member.cin)
        ws.cell(row=row_idx, column=5, value=member.phone_number)
        ws.cell(row=row_idx, column=6, value=member.get_status_display())
        ws.cell(row=row_idx, column=7, value=member.join_date.strftime("%d/%m/%Y"))
        ws.cell(row=row_idx, column=8, value=member.shares_count)

    return _to_buffer(wb)


def export_stock_movements_excel(
    cooperative: Cooperative, date_from: Optional[date] = None, date_to: Optional[date] = None
) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Mouvements de stock"
    _write_header(ws, ["Date", "Type", "Raison", "Produit", "Entrepôt", "Destination", "Quantité", "Référence"])

    movements = StockMovement.objects.filter(cooperative=cooperative).select_related(
        "product", "warehouse", "destination_warehouse"
    )
    if date_from:
        movements = movements.filter(created_at__date__gte=date_from)
    if date_to:
        movements = movements.filter(created_at__date__lte=date_to)

    for row_idx, movement in enumerate(movements.order_by("created_at"), start=2):
        ws.cell(row=row_idx, column=1, value=movement.created_at.strftime("%d/%m/%Y %H:%M"))
        ws.cell(row=row_idx, column=2, value=movement.get_movement_type_display())
        ws.cell(row=row_idx, column=3, value=movement.get_reason_display())
        ws.cell(row=row_idx, column=4, value=movement.product.sku)
        ws.cell(row=row_idx, column=5, value=movement.warehouse.code)
        ws.cell(row=row_idx, column=6, value=movement.destination_warehouse.code if movement.destination_warehouse else "")
        ws.cell(row=row_idx, column=7, value=float(movement.quantity))
        ws.cell(row=row_idx, column=8, value=movement.reference)

    return _to_buffer(wb)


def export_sales_orders_excel(
    cooperative: Cooperative, date_from: Optional[date] = None, date_to: Optional[date] = None
) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Commandes de vente"
    _write_header(ws, ["N° Commande", "Client", "Statut", "Date", "Montant total"])

    orders = SalesOrder.objects.filter(cooperative=cooperative).select_related("customer").prefetch_related("lines")
    if date_from:
        orders = orders.filter(order_date__gte=date_from)
    if date_to:
        orders = orders.filter(order_date__lte=date_to)

    for row_idx, order in enumerate(orders.order_by("order_date"), start=2):
        ws.cell(row=row_idx, column=1, value=order.order_number)
        ws.cell(row=row_idx, column=2, value=order.customer.name)
        ws.cell(row=row_idx, column=3, value=order.get_status_display())
        ws.cell(row=row_idx, column=4, value=order.order_date.strftime("%d/%m/%Y"))
        ws.cell(row=row_idx, column=5, value=float(order.total_amount))

    return _to_buffer(wb)
