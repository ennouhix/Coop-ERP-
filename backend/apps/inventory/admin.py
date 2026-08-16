from __future__ import annotations

from django.contrib import admin

from apps.inventory.models import StockLevel, StockMovement


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ["product", "warehouse", "quantity", "cooperative"]
    list_filter = ["cooperative", "warehouse"]
    search_fields = ["product__sku"]
    readonly_fields = [f.name for f in StockLevel._meta.fields]  # lecture seule : voir services.py

    def has_add_permission(self, request) -> bool:  # noqa: ANN001
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ANN001
        return False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        "movement_type",
        "reason",
        "product",
        "warehouse",
        "destination_warehouse",
        "quantity",
        "created_at",
    ]
    list_filter = ["movement_type", "reason", "cooperative"]
    search_fields = ["product__sku", "reference"]
    readonly_fields = [
        f.name for f in StockMovement._meta.fields
    ]  # ledger immuable : jamais éditable

    def has_add_permission(self, request) -> bool:  # noqa: ANN001
        return False  # créer un mouvement passe TOUJOURS par apps.inventory.services

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ANN001
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ANN001
        return False
