"""Serializer de sortie du tableau de bord (documente la structure pour Swagger)."""
from __future__ import annotations

from rest_framework import serializers


class PeriodSerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()


class MembersSummarySerializer(serializers.Serializer):
    active_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


class PartnersSummarySerializer(serializers.Serializer):
    active_customers = serializers.IntegerField()
    active_suppliers = serializers.IntegerField()


class SalesSummarySerializer(serializers.Serializer):
    orders_draft = serializers.IntegerField()
    orders_confirmed = serializers.IntegerField()
    orders_partially_delivered = serializers.IntegerField()
    orders_delivered = serializers.IntegerField()
    revenue_invoiced_period = serializers.DecimalField(max_digits=14, decimal_places=2)


class PurchasesSummarySerializer(serializers.Serializer):
    orders_draft = serializers.IntegerField()
    orders_confirmed = serializers.IntegerField()
    orders_partially_received = serializers.IntegerField()
    orders_received = serializers.IntegerField()
    spend_confirmed_period = serializers.DecimalField(max_digits=14, decimal_places=2)


class StockSummarySerializer(serializers.Serializer):
    total_stock_value = serializers.DecimalField(max_digits=14, decimal_places=2)
    low_stock_lines_count = serializers.IntegerField()


class BillingSummarySerializer(serializers.Serializer):
    total_outstanding_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_invoices_count = serializers.IntegerField()
    amount_collected_period = serializers.DecimalField(max_digits=14, decimal_places=2)


class DashboardSummarySerializer(serializers.Serializer):
    period = PeriodSerializer()
    members = MembersSummarySerializer()
    partners = PartnersSummarySerializer()
    sales = SalesSummarySerializer()
    purchases = PurchasesSummarySerializer()
    stock = StockSummarySerializer()
    billing = BillingSummarySerializer()
