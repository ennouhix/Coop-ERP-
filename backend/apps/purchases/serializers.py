"""
Serializers du module purchases.

Comme à l'Epic 8 : les champs produit/fournisseur/entrepôt des payloads
de création utilisent des UUIDField simples, résolus et vérifiés
(appartenance à la coopérative) explicitement dans la vue — jamais de
PrimaryKeyRelatedField(queryset=Model.objects.all()) déclaré en dur dans
un Serializer non généré par ModelSerializer (voir la docstring détaillée
dans apps/inventory/serializers.py pour le piège que ça évite).
"""
from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.purchases.models import PurchaseOrder, PurchaseOrderLine


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    quantity_remaining = serializers.DecimalField(max_digits=14, decimal_places=3, read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "id", "product", "product_sku", "product_name",
            "quantity_ordered", "quantity_received", "quantity_remaining",
            "unit_price", "line_total",
        ]
        read_only_fields = fields

    def get_product_name(self, obj: PurchaseOrderLine) -> str:
        from apps.core.fields import get_translated_value

        return get_translated_value(obj.product.name, "fr")


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "order_number", "supplier", "supplier_name", "warehouse", "warehouse_code",
            "status", "order_date", "expected_delivery_date", "notes",
            "lines", "total_amount", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "order_number", "status", "created_at", "updated_at"]


class PurchaseOrderLineInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity_ordered = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=Decimal("0.001"))
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    order_date = serializers.DateField()
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    lines = PurchaseOrderLineInputSerializer(many=True)

    def validate_lines(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError("Une commande doit contenir au moins une ligne.")
        return value


class PurchaseReceiptLineSerializer(serializers.Serializer):
    line_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=Decimal("0.001"))


class PurchaseReceiptSerializer(serializers.Serializer):
    receipts = PurchaseReceiptLineSerializer(many=True)

    def validate_receipts(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError("Au moins une ligne à réceptionner est requise.")
        return value
