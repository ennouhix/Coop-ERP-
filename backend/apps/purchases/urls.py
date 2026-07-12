from __future__ import annotations

from django.urls import path

from apps.purchases.views import (
    PurchaseOrderCancelView,
    PurchaseOrderConfirmView,
    PurchaseOrderDetailView,
    PurchaseOrderListCreateView,
    PurchaseOrderReceiveView,
)

app_name = "purchases"

urlpatterns = [
    path("orders/", PurchaseOrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<uuid:pk>/", PurchaseOrderDetailView.as_view(), name="order-detail"),
    path("orders/<uuid:order_id>/confirm/", PurchaseOrderConfirmView.as_view(), name="order-confirm"),
    path("orders/<uuid:order_id>/receive/", PurchaseOrderReceiveView.as_view(), name="order-receive"),
    path("orders/<uuid:order_id>/cancel/", PurchaseOrderCancelView.as_view(), name="order-cancel"),
]
