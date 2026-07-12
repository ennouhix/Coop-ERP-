from __future__ import annotations

from django.contrib import admin

from apps.purchases.models import PurchaseOrder, PurchaseOrderLine


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0
    readonly_fields = ["quantity_received"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "supplier", "warehouse", "status", "order_date", "cooperative"]
    list_filter = ["status", "cooperative"]
    search_fields = ["order_number"]
    readonly_fields = ["order_number", "created_at", "updated_at"]
    inlines = [PurchaseOrderLineInline]
