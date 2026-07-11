from __future__ import annotations

from django.contrib import admin

from apps.warehouses.models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "cooperative", "manager", "is_default"]
    list_filter = ["is_default", "cooperative"]
    search_fields = ["code", "name"]
    readonly_fields = ["code", "created_at", "updated_at"]
