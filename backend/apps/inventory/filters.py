"""Filtres pour les niveaux de stock et l'historique des mouvements."""

from __future__ import annotations

import django_filters

from apps.inventory.models import StockMovement, StockMovementReason, StockMovementType


class StockLevelFilter(django_filters.FilterSet):
    product = django_filters.UUIDFilter(field_name="product_id")
    warehouse = django_filters.UUIDFilter(field_name="warehouse_id")


class StockMovementFilter(django_filters.FilterSet):
    product = django_filters.UUIDFilter(field_name="product_id")
    warehouse = django_filters.UUIDFilter(field_name="warehouse_id")
    movement_type = django_filters.ChoiceFilter(choices=StockMovementType.choices)
    reason = django_filters.ChoiceFilter(choices=StockMovementReason.choices)
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = StockMovement
        fields = [
            "product",
            "warehouse",
            "movement_type",
            "reason",
            "created_after",
            "created_before",
        ]
