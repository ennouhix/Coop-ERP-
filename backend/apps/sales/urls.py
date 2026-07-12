from __future__ import annotations

from django.urls import path

from apps.sales.views import (
    SalesOrderCancelView,
    SalesOrderConfirmView,
    SalesOrderDeliverView,
    SalesOrderDetailView,
    SalesOrderListCreateView,
)

app_name = "sales"

urlpatterns = [
    path("orders/", SalesOrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<uuid:pk>/", SalesOrderDetailView.as_view(), name="order-detail"),
    path("orders/<uuid:order_id>/confirm/", SalesOrderConfirmView.as_view(), name="order-confirm"),
    path("orders/<uuid:order_id>/deliver/", SalesOrderDeliverView.as_view(), name="order-deliver"),
    path("orders/<uuid:order_id>/cancel/", SalesOrderCancelView.as_view(), name="order-cancel"),
]
