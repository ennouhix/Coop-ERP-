"""Serializers du module billing."""
from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.billing.models import Invoice, InvoiceLine, Payment, PaymentMethod


class InvoiceLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceLine
        fields = ["id", "product", "product_sku", "description", "quantity", "unit_price", "line_total"]
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "payment_date", "payment_method", "reference", "notes", "created_at"]
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    order_number = serializers.CharField(source="sales_order.order_number", read_only=True, default=None)
    lines = InvoiceLineSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "customer", "customer_name", "sales_order", "order_number",
            "status", "issue_date", "due_date", "notes",
            "lines", "payments", "total_amount", "amount_paid", "balance_due", "is_overdue",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "invoice_number", "status", "created_at", "updated_at"]


class InvoiceLineInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=Decimal("0.001"))
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))


class ManualInvoiceCreateSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    issue_date = serializers.DateField()
    due_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    lines = InvoiceLineInputSerializer(many=True)

    def validate_lines(self, value: list) -> list:
        if not value:
            raise serializers.ValidationError("Une facture doit contenir au moins une ligne.")
        return value


class InvoiceFromOrderSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    issue_date = serializers.DateField()
    due_date = serializers.DateField(required=False, allow_null=True)


class RecordPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    payment_date = serializers.DateField()
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
