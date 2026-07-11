from __future__ import annotations

from django.urls import path

from apps.warehouses.views import (
    WarehouseDeactivateView,
    WarehouseDetailView,
    WarehouseListCreateView,
    WarehouseReactivateView,
    WarehouseSetDefaultView,
)

app_name = "warehouses"

urlpatterns = [
    path("", WarehouseListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", WarehouseDetailView.as_view(), name="detail"),
    path("<uuid:warehouse_id>/set-default/", WarehouseSetDefaultView.as_view(), name="set-default"),
    path("<uuid:warehouse_id>/deactivate/", WarehouseDeactivateView.as_view(), name="deactivate"),
    path("<uuid:warehouse_id>/reactivate/", WarehouseReactivateView.as_view(), name="reactivate"),
]
