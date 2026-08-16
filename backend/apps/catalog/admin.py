from __future__ import annotations

from django.contrib import admin

from apps.catalog.models import Category, Product, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["name", "symbol", "unit_type", "cooperative"]
    list_filter = ["unit_type", "cooperative"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["__str__", "parent", "cooperative"]
    list_filter = ["cooperative"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "sku",
        "__str__",
        "category",
        "unit",
        "is_sellable",
        "is_purchasable",
        "cooperative",
    ]
    list_filter = ["is_sellable", "is_purchasable", "cooperative"]
    search_fields = ["sku", "barcode"]
    readonly_fields = ["sku", "created_at", "updated_at"]
