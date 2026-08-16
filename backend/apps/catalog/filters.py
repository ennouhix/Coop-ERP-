"""Filtres pour la liste des produits."""

from __future__ import annotations

import django_filters

from apps.catalog.models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.UUIDFilter(field_name="category_id")
    unit = django_filters.UUIDFilter(field_name="unit_id")
    is_sellable = django_filters.BooleanFilter()
    is_purchasable = django_filters.BooleanFilter()

    class Meta:
        model = Product
        fields = ["category", "unit", "is_sellable", "is_purchasable"]
