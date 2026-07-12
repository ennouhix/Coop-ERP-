from __future__ import annotations

from django.contrib import admin

from apps.sales.models import SalesOrder, SalesOrderLine


class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 0
    readonly_fields = ["quantity_delivered"]


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "customer", "warehouse", "status", "order_date", "cooperative"]
    list_filter = ["status", "cooperative"]
    search_fields = ["order_number"]
    readonly_fields = ["order_number", "created_at", "updated_at"]
    inlines = [SalesOrderLineInline]
