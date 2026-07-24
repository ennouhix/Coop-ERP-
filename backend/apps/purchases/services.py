"""
Logique métier du module purchases.

Le point le plus sensible : record_purchase_receipt() doit mettre à jour
PurchaseOrderLine.quantity_received ET créer le StockMovement (Epic 8)
dans LA MÊME TRANSACTION. Si l'un des deux échoue, aucun des deux ne doit
persister — sinon on se retrouve avec une commande qui dit "reçu" sans
stock physique, ou l'inverse.
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
from apps.purchases.models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from apps.warehouses.models import Warehouse

ORDER_NUMBER_PADDING = 5


class PurchaseOrderError(Exception):
    """Erreur métier générique (message destiné à être affiché tel quel)."""


@dataclass(frozen=True)
class PurchaseLineInput:
    product_id: str
    quantity_ordered: Decimal
    unit_price: Decimal


@transaction.atomic
def _generate_order_number(cooperative: Cooperative) -> str:
    Cooperative.objects.select_for_update().get(pk=cooperative.pk)

    last_order = (
        PurchaseOrder.all_objects.filter(cooperative=cooperative, order_number__startswith="PO-")
        .order_by("-order_number")
        .first()
    )
    if last_order is None:
        next_sequence = 1
    else:
        try:
            next_sequence = int(last_order.order_number.split("-")[-1]) + 1
        except ValueError:
            next_sequence = PurchaseOrder.all_objects.filter(cooperative=cooperative).count() + 1

    return f"PO-{str(next_sequence).zfill(ORDER_NUMBER_PADDING)}"


@transaction.atomic
def create_purchase_order(
    *, cooperative: Cooperative, supplier: Partner, warehouse: Warehouse, lines: list, actor,  # noqa: ANN001
    order_date: date, expected_delivery_date: Optional[date] = None, notes: str = "",
) -> PurchaseOrder:
    if not supplier.is_supplier:
        raise PurchaseOrderError("Ce partenaire n'est pas enregistré comme fournisseur.")
    if not lines:
        raise PurchaseOrderError("Une commande d'achat doit contenir au moins une ligne.")

    order = PurchaseOrder.objects.create(
        cooperative=cooperative,
        order_number=_generate_order_number(cooperative),
        supplier=supplier, warehouse=warehouse,
        status=PurchaseOrderStatus.DRAFT,
        order_date=order_date, expected_delivery_date=expected_delivery_date,
        notes=notes, created_by=actor,
    )

    for line in lines:
        PurchaseOrderLine.objects.create(
            cooperative=cooperative, purchase_order=order,
            product=line["product"], quantity_ordered=line["quantity_ordered"],
            unit_price=line["unit_price"], created_by=actor,
        )

    return order


@transaction.atomic
def confirm_purchase_order(*, order: PurchaseOrder, actor) -> PurchaseOrder:  # noqa: ANN001
    if order.status != PurchaseOrderStatus.DRAFT:
        raise PurchaseOrderError("Seule une commande en brouillon peut être confirmée.")

    order.status = PurchaseOrderStatus.CONFIRMED
    order.updated_by = actor
    order.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=order.cooperative, actor=actor, action="purchase_order.confirmed",
        target_type="PurchaseOrder", target_id=order.id, target_repr=order.order_number,
    )
    return order


@transaction.atomic
def cancel_purchase_order(*, order: PurchaseOrder, actor) -> PurchaseOrder:  # noqa: ANN001
    if order.status not in {PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.CONFIRMED}:
        raise PurchaseOrderError("Cette commande ne peut plus être annulée (déjà reçue ou annulée).")
    if order.has_any_receipt:
        raise PurchaseOrderError("Impossible d'annuler une commande déjà partiellement réceptionnée.")

    order.status = PurchaseOrderStatus.CANCELLED
    order.updated_by = actor
    order.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=order.cooperative, actor=actor, action="purchase_order.cancelled",
        target_type="PurchaseOrder", target_id=order.id, target_repr=order.order_number,
    )
    return order


@transaction.atomic
def record_purchase_receipt(*, order: PurchaseOrder, actor, receipts: list) -> PurchaseOrder:  # noqa: ANN001
    """
    `receipts` : liste de {"line_id": UUID, "quantity": Decimal}.
    Pour chaque ligne, incrémente quantity_received et crée le
    StockMovement d'entrée correspondant (Epic 8), dans une transaction
    unique couvrant tout le lot de réception.
    """
    if order.status not in {PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.PARTIALLY_RECEIVED}:
        raise PurchaseOrderError("Seule une commande confirmée peut être réceptionnée.")

    lines_by_id = {str(line.id): line for line in order.lines.select_for_update()}

    for receipt in receipts:
        line = lines_by_id.get(str(receipt["line_id"]))
        if line is None:
            raise PurchaseOrderError("Ligne de commande introuvable sur cette commande.")

        quantity = receipt["quantity"]
        if quantity <= 0:
            raise PurchaseOrderError("La quantité réceptionnée doit être positive.")
        if quantity > line.quantity_remaining:
            raise PurchaseOrderError(
                f"Quantité réceptionnée ({quantity}) supérieure au reliquat "
                f"({line.quantity_remaining}) pour {line.product.sku}."
            )

        inventory_services.record_stock_in(
            product=line.product, warehouse=order.warehouse, quantity=quantity, actor=actor,
            reason=StockMovementReason.PURCHASE, reference=order.order_number,
            notes=f"Réception commande {order.order_number}",
        )

        line.quantity_received += quantity
        line.save(update_fields=["quantity_received"])

    order.refresh_from_db()
    order.status = PurchaseOrderStatus.RECEIVED if order.is_fully_received else PurchaseOrderStatus.PARTIALLY_RECEIVED
    order.updated_by = actor
    order.save(update_fields=["status", "updated_by"])

    log_activity(
        cooperative=order.cooperative, actor=actor, action="purchase_order.received",
        target_type="PurchaseOrder", target_id=order.id, target_repr=order.order_number,
        metadata={"receipts": [{"line_id": str(r["line_id"]), "quantity": str(r["quantity"])} for r in receipts], "new_status": order.status},
    )
    return order
