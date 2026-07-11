from __future__ import annotations

from django.urls import path

from apps.catalog.views import (
    CategoryDetailView,
    CategoryListCreateView,
    ProductDeactivateView,
    ProductDetailView,
    ProductListCreateView,
    ProductReactivateView,
    UnitDetailView,
    UnitListCreateView,
)

app_name = "catalog"

urlpatterns = [
    path("units/", UnitListCreateView.as_view(), name="unit-list-create"),
    path("units/<uuid:pk>/", UnitDetailView.as_view(), name="unit-detail"),
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<uuid:pk>/", CategoryDetailView.as_view(), name="category-detail"),
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/<uuid:product_id>/deactivate/", ProductDeactivateView.as_view(), name="product-deactivate"),
    path("products/<uuid:product_id>/reactivate/", ProductReactivateView.as_view(), name="product-reactivate"),
]
