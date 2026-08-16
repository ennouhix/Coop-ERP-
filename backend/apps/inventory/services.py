"""
Logique métier du module inventory — la partie la plus sensible du projet
à ce stade : toute erreur ici peut désynchroniser le stock réel de ce que
dit le logiciel, ou pire, laisser un stock passer négatif sous concurrence.

Principe : StockMovement (immuable) est TOUJOURS créé dans la même
transaction que la mise à jour de StockLevel (dénormalisé). Jamais l'un
sans l'autre.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.audit.services import log_activity
from apps.catalog.models import Product
from apps.inventory.models import StockLevel, StockMovement, StockMovementReason, StockMovementType
from apps.warehouses.models import Warehouse


class InsufficientStockError(Exception):
    """Le mouvement demandé ferait passer le stock sous zéro."""


class InvalidMovementError(Exception):
    """Paramètres de mouvement invalides (quantité négative, entrepôts identiques...)."""


def _get_or_create_locked_stock_level(*, product: Product, warehouse: Warehouse) -> StockLevel:
    """
    Retourne la ligne StockLevel verrouillée (select_for_update) pour ce
    couple produit/entrepôt, en la créant si elle n'existe pas encore.

    Gère la race condition où deux transactions concurrentes tenteraient
    de créer la même ligne pour la première fois : la deuxième échoue sur
    la contrainte unique, on la relit alors avec verrou (elle existe déjà
    à ce stade grâce à la première transaction).
    """
    try:
        return StockLevel.objects.select_for_update().get(product=product, warehouse=warehouse)
    except StockLevel.DoesNotExist:
        try:
            with transaction.atomic():  # savepoint : isole l'éventuel IntegrityError
                return StockLevel.objects.create(
                    cooperative=product.cooperative,
                    product=product,
                    warehouse=warehouse,
                    quantity=Decimal("0"),
                )
        except IntegrityError:
            return StockLevel.objects.select_for_update().get(product=product, warehouse=warehouse)


def _validate_quantity(quantity: Decimal) -> None:
    if quantity <= 0:
        raise InvalidMovementError("La quantité doit être strictement positive.")


@transaction.atomic
def record_stock_in(
    *,
    product: Product,
    warehouse: Warehouse,
    quantity: Decimal,
    actor,  # noqa: ANN001
    reason: str = StockMovementReason.ADJUSTMENT,
    reference: str = "",
    notes: str = "",
) -> StockMovement:
    _validate_quantity(quantity)

    level = _get_or_create_locked_stock_level(product=product, warehouse=warehouse)
    level.quantity += quantity
    level.save(update_fields=["quantity"])

    movement = StockMovement.objects.create(
        cooperative=product.cooperative,
        movement_type=StockMovementType.IN,
        reason=reason,
        product=product,
        warehouse=warehouse,
        quantity=quantity,
        reference=reference,
        notes=notes,
        created_by=actor,
    )
    log_activity(
        cooperative=product.cooperative,
        actor=actor,
        action="stock.in",
        target_type="StockMovement",
        target_id=movement.id,
        target_repr=f"{product.sku} +{quantity} @ {warehouse.code}",
        metadata={"reason": reason, "reference": reference},
    )
    return movement


@transaction.atomic
def record_stock_out(
    *,
    product: Product,
    warehouse: Warehouse,
    quantity: Decimal,
    actor,  # noqa: ANN001
    reason: str = StockMovementReason.ADJUSTMENT,
    reference: str = "",
    notes: str = "",
) -> StockMovement:
    _validate_quantity(quantity)

    level = _get_or_create_locked_stock_level(product=product, warehouse=warehouse)
    if level.quantity < quantity:
        raise InsufficientStockError(
            f"Stock insuffisant : {level.quantity} {product.unit.symbol} disponible(s), "
            f"{quantity} {product.unit.symbol} demandé(s)."
        )

    level.quantity -= quantity
    level.save(update_fields=["quantity"])

    movement = StockMovement.objects.create(
        cooperative=product.cooperative,
        movement_type=StockMovementType.OUT,
        reason=reason,
        product=product,
        warehouse=warehouse,
        quantity=quantity,
        reference=reference,
        notes=notes,
        created_by=actor,
    )
    log_activity(
        cooperative=product.cooperative,
        actor=actor,
        action="stock.out",
        target_type="StockMovement",
        target_id=movement.id,
        target_repr=f"{product.sku} -{quantity} @ {warehouse.code}",
        metadata={"reason": reason, "reference": reference},
    )
    return movement


@transaction.atomic
def record_stock_transfer(
    *,
    product: Product,
    from_warehouse: Warehouse,
    to_warehouse: Warehouse,
    quantity: Decimal,
    actor,  # noqa: ANN001
    reference: str = "",
    notes: str = "",
) -> StockMovement:
    if from_warehouse.pk == to_warehouse.pk:
        raise InvalidMovementError(
            "L'entrepôt source et l'entrepôt destination doivent être différents."
        )
    _validate_quantity(quantity)

    # Verrou toujours pris dans le même ordre (par pk d'entrepôt croissant)
    # pour empêcher un deadlock entre deux transferts concurrents en sens
    # opposé (A->B en même temps que B->A).
    warehouses_by_pk = sorted([from_warehouse, to_warehouse], key=lambda w: str(w.pk))
    locked = {
        w.pk: _get_or_create_locked_stock_level(product=product, warehouse=w)
        for w in warehouses_by_pk
    }

    source_level = locked[from_warehouse.pk]
    dest_level = locked[to_warehouse.pk]

    if source_level.quantity < quantity:
        raise InsufficientStockError(
            f"Stock insuffisant dans l'entrepôt source : "
            f"{source_level.quantity} {product.unit.symbol} disponible(s)."
        )

    source_level.quantity -= quantity
    source_level.save(update_fields=["quantity"])
    dest_level.quantity += quantity
    dest_level.save(update_fields=["quantity"])

    movement = StockMovement.objects.create(
        cooperative=product.cooperative,
        movement_type=StockMovementType.TRANSFER,
        reason=StockMovementReason.TRANSFER,
        product=product,
        warehouse=from_warehouse,
        destination_warehouse=to_warehouse,
        quantity=quantity,
        reference=reference,
        notes=notes,
        created_by=actor,
    )
    log_activity(
        cooperative=product.cooperative,
        actor=actor,
        action="stock.transfer",
        target_type="StockMovement",
        target_id=movement.id,
        target_repr=f"{product.sku} {quantity} {from_warehouse.code} -> {to_warehouse.code}",
        metadata={"reference": reference},
    )
    return movement


def get_current_quantity(*, product: Product, warehouse: Warehouse) -> Decimal:
    """Lecture simple, sans verrou (pas de modification en cours)."""
    level = StockLevel.objects.filter(product=product, warehouse=warehouse).first()
    return level.quantity if level else Decimal("0")
