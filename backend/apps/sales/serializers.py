"""Serializers du module sales — même précaution FK que purchases/inventory."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.sales.models import SalesOrder, SalesOrderLine


class SalesOrderLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.SerializerMethodField()
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    quantity_remaining = serializers.DecimalField(max_digits=14, decimal_places=3, read_only=True)

    class Meta:
        model = SalesOrderLine
        fields = [
            "id",
            "product",
            "product_sku",
            "product_name",
            "quantity_ordered",
            "quantity_delivered",
            "quantity_remaining",
            "unit_price",
            "line_total",
        ]
        read_only_fields = fields

    def get_product_name(self, obj: SalesOrderLine) -> str:
        from apps.core.fields import get_translated_value

        return get_translated_value(obj.product.name, "fr")


class SalesOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    lines = SalesOrderLineSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = SalesOrder
        fields = [
            "id",
            "order_number",
            "customer",
            "customer_name",
            "warehouse",
            "warehouse_code",
            "status",
            "order_date",
            "expected_delivery_date",
            "notes",
            "lines",
            "total_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "order_number", "status", "created_at", "updated_at"]


class SalesOrderLineInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity_ordered = serializers.DecimalField(
        max_digits=14, decimal_places=3, min_value=Decimal("0.001")
    )
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))


class SalesOrderCreateSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    order_date = serializers.DateField()
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    lines = SalesOrderLineInputSerializer(many=True)

    def validate_lines(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError("Une commande doit contenir au moins une ligne.")
        return value


class SalesDeliveryLineSerializer(serializers.Serializer):
    line_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=Decimal("0.001"))


class SalesDeliverySerializer(serializers.Serializer):
    deliveries = SalesDeliveryLineSerializer(many=True)

    def validate_deliveries(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError("Au moins une ligne à livrer est requise.")
        return value
