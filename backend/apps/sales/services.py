"""
Logique métier du module sales.

record_sales_delivery() met à jour SalesOrderLine.quantity_delivered ET
appelle apps.inventory.services.record_stock_out() dans LA MÊME
TRANSACTION — le stock ne doit jamais être décrémenté sans que la ligne
de commande reflète la même quantité livrée, et inversement.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from django.db import transaction

from apps.audit.services import log_activity
from apps.cooperatives.models import Cooperative
from apps.inventory import services as inventory_services
from apps.inventory.models import StockMovementReason
from apps.partners.models import Partner
from apps.sales.models import SalesOrder, SalesOrderLine, SalesOrderStatus
from apps.warehouses.models import Warehouse

ORDER_NUMBER_PADDING = 5


class SalesOrderError(Exception):
    """Erreur métier générique (message destiné à être affiché tel quel)."""


@dataclass(frozen=True)
class SalesLineInput:
    product_id: str
    quantity_ordered: Decimal
    unit_price: Decimal


@transaction.atomic
def _generate_order_number(cooperative: Cooperative) -> str:
    Cooperative.objects.select_for_update().get(pk=cooperative.pk)

    last_order = (
        SalesOrder.all_objects.filter(cooperative=cooperative, order_number__startswith="SO-")
        .order_by("-order_number")
        .first()
    )
    if last_order is None:
        next_sequence = 1
    else:
        try:
            next_sequence = int(last_order.order_number.split("-")[-1]) + 1
        except ValueError:
            next_sequence = SalesOrder.all_objects.filter(cooperative=cooperative).count() + 1

    return f"SO-{str(next_sequence).zfill(ORDER_NUMBER_PADDING)}"


def _compute_outstanding_balance(customer: Partner, *, exclude_order_id: Optional[str] = None) -> Decimal:
    """
    Approximation V1 de l'encours client : somme des commandes non
    annulées et non totalement soldées. À remplacer par l'encours facturé
    réel une fois la Facturation (Epic 11) livrée — ce calcul reste une
    approximation raisonnable en attendant.
    """
    orders = SalesOrder.objects.filter(
        customer=customer,
        status__in=[SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIALLY_DELIVERED, SalesOrderStatus.DELIVERED],
    )
    if exclude_order_id:
        orders = orders.exclude(pk=exclude_order_id)
    return sum((o.total_amount for o in orders), Decimal("0"))


@transaction.atomic
def create_sales_order(
    *, cooperative: Cooperative, customer: Partner, warehouse: Warehouse, lines: list, actor,  # noqa: ANN001
    order_date: date, expected_delivery_date: Optional[date] = None, notes: str = "",
) -> SalesOrder:
    if not customer.is_customer:
        raise SalesOrderError("Ce partenaire n'est pas enregistré comme client.")
    if not lines:
        raise SalesOrderError("Une commande de vente doit contenir au moins une ligne.")

    order = SalesOrder.objects.create(
        cooperative=cooperative,
        order_number=_generate_order_number(cooperative),
        customer=customer, warehouse=warehouse,
        status=SalesOrderStatus.DRAFT,
        order_date=order_date, expected_delivery_date=expected_delivery_date,
        notes=notes, created_by=actor,
    )

    for line in lines:
        SalesOrderLine.objects.create(
            cooperative=cooperative, sales_order=order,
            product=line["product"], quantity_ordered=line["quantity_ordered"],
            unit_price=line["unit_price"], created_by=actor,
        )

    return order


@transaction.atomic
def confirm_sales_order(*, order: SalesOrder, actor) -> SalesOrder:  # noqa: ANN001
    if order.status != SalesOrderStatus.DRAFT:
        raise SalesOrderError("Seule une commande en brouillon peut être confirmée.")

    customer = order.customer
    if customer.credit_limit and customer.credit_limit > 0:
        outstanding = _compute_outstanding_balance(customer, exclude_order_id=order.pk)
        if outstanding + order.total_amount > customer.credit_limit:
            raise SalesOrderError(
                f"Cette confirmation dépasserait la limite de crédit du client "
                f"({customer.credit_limit} — encours actuel {outstanding})."
            )

    order.status = SalesOrderStatus.CONFIRMED
    order.updated_by = actor
    order.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=order.cooperative, actor=actor, action="sales_order.confirmed",
        target_type="SalesOrder", target_id=order.id, target_repr=order.order_number,
    )
    return order


@transaction.atomic
def cancel_sales_order(*, order: SalesOrder, actor) -> SalesOrder:  # noqa: ANN001
    if order.status not in {SalesOrderStatus.DRAFT, SalesOrderStatus.CONFIRMED}:
        raise SalesOrderError("Cette commande ne peut plus être annulée (déjà livrée ou annulée).")
    if order.has_any_delivery:
        raise SalesOrderError("Impossible d'annuler une commande déjà partiellement livrée.")

    order.status = SalesOrderStatus.CANCELLED
    order.updated_by = actor
    order.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=order.cooperative, actor=actor, action="sales_order.cancelled",
        target_type="SalesOrder", target_id=order.id, target_repr=order.order_number,
    )
    return order


@transaction.atomic
def record_sales_delivery(*, order: SalesOrder, actor, deliveries: list) -> SalesOrder:  # noqa: ANN001
    """
    `deliveries` : liste de {"line_id": UUID, "quantity": Decimal}.
    Propage InsufficientStockError si le stock disponible ne suffit pas
    (aucune vente à découvert en V1).
    """
    if order.status not in {SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIALLY_DELIVERED}:
        raise SalesOrderError("Seule une commande confirmée peut être livrée.")

    lines_by_id = {str(line.id): line for line in order.lines.select_for_update()}

    for delivery in deliveries:
        line = lines_by_id.get(str(delivery["line_id"]))
        if line is None:
            raise SalesOrderError("Ligne de commande introuvable sur cette commande.")

        quantity = delivery["quantity"]
        if quantity <= 0:
            raise SalesOrderError("La quantité livrée doit être positive.")
        if quantity > line.quantity_remaining:
            raise SalesOrderError(
                f"Quantité livrée ({quantity}) supérieure au reliquat "
                f"({line.quantity_remaining}) pour {line.product.sku}."
            )

        try:
            inventory_services.record_stock_out(
                product=line.product, warehouse=order.warehouse, quantity=quantity, actor=actor,
                reason=StockMovementReason.SALE, reference=order.order_number,
                notes=f"Livraison commande {order.order_number}",
            )
        except inventory_services.InsufficientStockError as exc:
            raise SalesOrderError(str(exc)) from exc

        line.quantity_delivered += quantity
        line.save(update_fields=["quantity_delivered"])

    order.refresh_from_db()
    order.status = SalesOrderStatus.DELIVERED if order.is_fully_delivered else SalesOrderStatus.PARTIALLY_DELIVERED
    order.updated_by = actor
    order.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=order.cooperative, actor=actor, action="sales_order.delivered",
        target_type="SalesOrder", target_id=order.id, target_repr=order.order_number,
        metadata={"deliveries": [{"line_id": str(d["line_id"]), "quantity": str(d["quantity"])} for d in deliveries], "new_status": order.status},
    )
    return order
