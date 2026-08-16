from __future__ import annotations

from django.urls import path

from apps.documents.views import (
    DeliveryNotePdfView,
    DocumentTemplateDetailView,
    DocumentTemplateListView,
    PurchaseOrderPdfView,
    ReceiptPdfView,
)

app_name = "documents"

urlpatterns = [
    path(
        "delivery-notes/<uuid:order_id>/pdf/",
        DeliveryNotePdfView.as_view(),
        name="delivery-note-pdf",
    ),
    path(
        "purchase-orders/<uuid:order_id>/pdf/",
        PurchaseOrderPdfView.as_view(),
        name="purchase-order-pdf",
    ),
    path("receipts/<uuid:order_id>/pdf/", ReceiptPdfView.as_view(), name="receipt-pdf"),
    path("templates/", DocumentTemplateListView.as_view(), name="document-templates"),
    path(
        "templates/<str:template_type>/",
        DocumentTemplateDetailView.as_view(),
        name="document-template-detail",
    ),
]
