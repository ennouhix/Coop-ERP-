"""
Logique métier du module warehouses.
"""
from __future__ import annotations

from django.db import transaction

from apps.cooperatives.models import Cooperative
from apps.warehouses.models import Warehouse

CODE_PADDING = 4


@transaction.atomic
def generate_warehouse_code(cooperative: Cooperative) -> str:
    Cooperative.objects.select_for_update().get(pk=cooperative.pk)

    last_warehouse = (
        Warehouse.all_objects.filter(cooperative=cooperative, code__startswith="WH-")
        .order_by("-code")
        .first()
    )

    if last_warehouse is None:
        next_sequence = 1
    else:
        try:
            next_sequence = int(last_warehouse.code.split("-")[-1]) + 1
        except ValueError:
            next_sequence = Warehouse.all_objects.filter(cooperative=cooperative).count() + 1

    return f"WH-{str(next_sequence).zfill(CODE_PADDING)}"


@transaction.atomic
def create_warehouse(*, cooperative: Cooperative, **fields) -> Warehouse:
    code = generate_warehouse_code(cooperative)

    # Le tout premier entrepôt d'une coopérative devient automatiquement le
    # défaut : une coopérative qui a au moins un entrepôt ne doit jamais se
    # retrouver sans entrepôt par défaut.
    is_first_warehouse = not Warehouse.all_objects.filter(cooperative=cooperative).exists()
    requested_default = fields.pop("is_default", False)

    warehouse = Warehouse.objects.create(
        cooperative=cooperative, code=code, is_default=is_first_warehouse, **fields
    )

    if requested_default and not is_first_warehouse:
        set_default_warehouse(warehouse=warehouse)

    return warehouse


@transaction.atomic
def set_default_warehouse(*, warehouse: Warehouse) -> None:
    """
    Verrouille tous les entrepôts de la coopérative le temps de désactiver
    l'ancien défaut et d'activer le nouveau — évite qu'une requête
    concurrente ne laisse deux entrepôts marqués défaut simultanément.
    """
    Warehouse.all_objects.select_for_update().filter(cooperative_id=warehouse.cooperative_id).update(
        is_default=False
    )
    warehouse.is_default = True
    warehouse.save(update_fields=["is_default"])
