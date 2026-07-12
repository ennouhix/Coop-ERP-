from __future__ import annotations

from django.urls import path

from apps.inventory.views import (
    LowStockListView,
    StockLevelListView,
    StockMovementInView,
    StockMovementListView,
    StockMovementOutView,
    StockMovementTransferView,
)

app_name = "inventory"

urlpatterns = [
    path("stock-levels/", StockLevelListView.as_view(), name="stock-level-list"),
    path("stock-levels/low-stock/", LowStockListView.as_view(), name="low-stock-list"),
    path("movements/", StockMovementListView.as_view(), name="movement-list"),
    path("movements/in/", StockMovementInView.as_view(), name="movement-in"),
    path("movements/out/", StockMovementOutView.as_view(), name="movement-out"),
    path("movements/transfer/", StockMovementTransferView.as_view(), name="movement-transfer"),
]
