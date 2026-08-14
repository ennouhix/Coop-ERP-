"""
Vues du module documents (M16).

Endpoints de téléchargement des documents commerciaux (PDF archivés) :
- GET /api/v1/documents/delivery-notes/{order_id}/pdf/
- GET /api/v1/documents/purchase-orders/{order_id}/pdf/
- GET /api/v1/documents/receipts/{order_id}/pdf/

Personnalisation des modèles (un par type de document) :
- GET /api/v1/documents/templates/                    -> liste des 3 types + personnalisation
- PUT /api/v1/documents/templates/{template_type}/    -> crée ou met à jour la personnalisation

Les permissions s'appuient sur le module RBAC `documents`
(documents.view pour les téléchargements, documents.edit pour les modèles).
"""
from __future__ import annotations

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsCooperativeMember
from apps.documents import services
from apps.documents.models import DocumentTemplate, DocumentTemplateType
from apps.documents.serializers import DocumentTemplateSerializer, DocumentTemplateTypeSerializer
from apps.purchases.models import PurchaseOrder
from apps.roles_permissions.permissions import RequirePermission
from apps.sales.models import SalesOrder


def _pdf_response(archive) -> HttpResponse:  # noqa: ANN001
    response = HttpResponse(archive.pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{archive.filename}"'
    return response


class DeliveryNotePdfView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("documents.view")]

    def get(self, request: Request, order_id: str) -> HttpResponse:
        order = get_object_or_404(
            SalesOrder.objects.select_related("cooperative"),
            pk=order_id, cooperative_id=request.user.cooperative_id,
        )
        archive = services.generate_document(
            order, DocumentTemplateType.DELIVERY_NOTE, actor=request.user
        )
        return _pdf_response(archive)


class PurchaseOrderPdfView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("documents.view")]

    def get(self, request: Request, order_id: str) -> HttpResponse:
        order = get_object_or_404(
            PurchaseOrder.objects.select_related("cooperative"),
            pk=order_id, cooperative_id=request.user.cooperative_id,
        )
        archive = services.generate_document(
            order, DocumentTemplateType.PURCHASE_ORDER, actor=request.user
        )
        return _pdf_response(archive)


class ReceiptPdfView(APIView):
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("documents.view")]

    def get(self, request: Request, order_id: str) -> HttpResponse:
        order = get_object_or_404(
            PurchaseOrder.objects.select_related("cooperative"),
            pk=order_id, cooperative_id=request.user.cooperative_id,
        )
        archive = services.generate_document(
            order, DocumentTemplateType.RECEIPT, actor=request.user
        )
        return _pdf_response(archive)


class DocumentTemplateListView(APIView):
    """Les 3 types de documents avec leur personnalisation (ou les valeurs par défaut)."""

    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("documents.view")]

    def get(self, request: Request) -> Response:
        cooperative_id = request.user.cooperative_id
        templates = {
            t.template_type: t
            for t in DocumentTemplate.objects.filter(cooperative_id=cooperative_id)
        }
        data = []
        for template_type in DocumentTemplateType.values:
            instance = templates.get(template_type)
            if instance is None:
                data.append(DocumentTemplateTypeSerializer({
                    "template_type": template_type,
                    "template_type_label": DocumentTemplateType(template_type).label,
                }).data)
            else:
                data.append(DocumentTemplateSerializer(instance).data)
        return Response(data)


class DocumentTemplateDetailView(APIView):
    """Crée ou met à jour la personnalisation d'un type de document (upsert)."""

    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("documents.edit")]

    def put(self, request: Request, template_type: str) -> Response:
        if template_type not in DocumentTemplateType.values:
            return Response(
                {"error": {"message": "Type de document inconnu."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cooperative_id = request.user.cooperative_id
        template = DocumentTemplate.objects.filter(
            cooperative_id=cooperative_id, template_type=template_type,
        ).first()

        serializer = DocumentTemplateSerializer(
            template, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        if template is None:
            template = DocumentTemplate(
                cooperative_id=cooperative_id, template_type=template_type,
                created_by=request.user,
            )
        template = serializer.save(
            template_type=template_type, cooperative_id=cooperative_id,
            updated_by=request.user,
        )
        return Response(DocumentTemplateSerializer(template).data, status=status.HTTP_200_OK)
