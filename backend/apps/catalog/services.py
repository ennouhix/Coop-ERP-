"""
Logique métier du catalogue. Même stratégie de verrouillage que
apps.members/apps.partners.services pour la génération de code séquentiel.
"""

from __future__ import annotations

from django.db import transaction

from apps.catalog.models import Category, Product
from apps.cooperatives.models import Cooperative

SKU_PADDING = 5


@transaction.atomic
def generate_product_sku(cooperative: Cooperative) -> str:
    Cooperative.objects.select_for_update().get(pk=cooperative.pk)

    last_product = (
        Product.all_objects.filter(cooperative=cooperative, sku__startswith="PRD-")
        .order_by("-sku")
        .first()
    )

    if last_product is None:
        next_sequence = 1
    else:
        try:
            next_sequence = int(last_product.sku.split("-")[-1]) + 1
        except ValueError:
            next_sequence = Product.all_objects.filter(cooperative=cooperative).count() + 1

    return f"PRD-{str(next_sequence).zfill(SKU_PADDING)}"


@transaction.atomic
def create_product(*, cooperative: Cooperative, **fields) -> Product:
    sku = generate_product_sku(cooperative)
    return Product.objects.create(cooperative=cooperative, sku=sku, **fields)


def assert_category_hierarchy_valid(category: Category) -> None:
    """Point d'entrée explicite pour valider une catégorie avant sauvegarde."""
    category.full_clean()
