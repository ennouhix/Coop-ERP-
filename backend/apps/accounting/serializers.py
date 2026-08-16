"""
Serializers du module Comptabilité / Trésorerie.

Hiérarchie :
- AccountSerializer        : plan comptable
- JournalSerializer        : journaux
- AccountingEntryLineSerializer
- AccountingEntrySerializer : écriture avec lignes imbriquées (lecture)
- AccountingEntryCreateSerializer : création (écriture + lignes en input)
- GeneralLedgerRowSerializer : grand livre (agrégation par compte)
- TrialBalanceRowSerializer  : balance des comptes
"""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.accounting.models import Account, AccountingEntry, AccountingEntryLine, Journal
from apps.core.fields import get_translated_value


class AccountSerializer(serializers.ModelSerializer):
    name_display = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            "id",
            "code",
            "name",
            "name_display",
            "account_type",
            "parent",
            "is_system",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def get_name_display(self, obj: Account) -> str:
        return get_translated_value(obj.name, "fr")

    def validate_name(self, value):  # noqa: ANN001
        if isinstance(value, str):
            return {"fr": value, "ar": ""}
        if isinstance(value, dict):
            return {"fr": value.get("fr", ""), "ar": value.get("ar", "")}
        return value


class JournalSerializer(serializers.ModelSerializer):
    name_display = serializers.SerializerMethodField()

    class Meta:
        model = Journal
        fields = ["id", "code", "name", "name_display", "journal_type"]
        read_only_fields = ["id"]

    def get_name_display(self, obj: Journal) -> str:
        return get_translated_value(obj.name, "fr")


class AccountingEntryLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source="account.code", read_only=True)
    account_name = serializers.SerializerMethodField()

    class Meta:
        model = AccountingEntryLine
        fields = [
            "id",
            "account",
            "account_code",
            "account_name",
            "label",
            "debit",
            "credit",
        ]
        read_only_fields = fields

    def get_account_name(self, obj: AccountingEntryLine) -> str:
        return get_translated_value(obj.account.name, "fr")


class AccountingEntrySerializer(serializers.ModelSerializer):
    journal_code = serializers.CharField(source="journal.code", read_only=True)
    lines = AccountingEntryLineSerializer(many=True, read_only=True)
    total_debit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_credit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)

    class Meta:
        model = AccountingEntry
        fields = [
            "id",
            "journal",
            "journal_code",
            "entry_number",
            "entry_date",
            "period",
            "description",
            "is_posted",
            "lines",
            "total_debit",
            "total_credit",
            "is_balanced",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "journal_code",
            "entry_number",
            "period",
            "is_posted",
            "total_debit",
            "total_credit",
            "is_balanced",
            "created_at",
            "updated_at",
        ]


# ---- Input serializers ----


class AccountingEntryLineInputSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    label = serializers.CharField(required=False, allow_blank=True, default="")
    debit = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
    )
    credit = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
        default=Decimal("0"),
    )

    def validate(self, data: dict) -> dict:
        if data["debit"] > 0 and data["credit"] > 0:
            raise serializers.ValidationError(
                "Une ligne ne peut pas avoir à la fois un débit et un crédit non nuls."
            )
        return data


class AccountingEntryCreateSerializer(serializers.Serializer):
    journal_id = serializers.UUIDField()
    entry_date = serializers.DateField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    lines = AccountingEntryLineInputSerializer(many=True)

    def validate_lines(self, value: list) -> list:
        if len(value) < 2:
            raise serializers.ValidationError("Une écriture doit contenir au moins deux lignes.")
        return value


# ---- Read-only report serializers ----


class GeneralLedgerRowSerializer(serializers.Serializer):
    entry_number = serializers.CharField()
    entry_date = serializers.DateField()
    journal_code = serializers.CharField()
    description = serializers.CharField()
    debit = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit = serializers.DecimalField(max_digits=14, decimal_places=2)
    running_balance = serializers.DecimalField(max_digits=14, decimal_places=2)


class TrialBalanceRowSerializer(serializers.Serializer):
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    debit_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    debit_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit_balance = serializers.DecimalField(max_digits=14, decimal_places=2)


class AccountingDashboardSerializer(serializers.Serializer):
    revenue_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    expense_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_result = serializers.DecimalField(max_digits=14, decimal_places=2)
    treasury_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    draft_entries_count = serializers.IntegerField()
    posted_entries_count = serializers.IntegerField()
    recent_entries = AccountingEntrySerializer(many=True)


class FinancialStatementItemSerializer(serializers.Serializer):
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    debit = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class CPCSerializer(serializers.Serializer):
    revenues = FinancialStatementItemSerializer(many=True)
    expenses = FinancialStatementItemSerializer(many=True)
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_result = serializers.DecimalField(max_digits=14, decimal_places=2)


class BilanSerializer(serializers.Serializer):
    assets = FinancialStatementItemSerializer(many=True)
    liabilities = FinancialStatementItemSerializer(many=True)
    equity = FinancialStatementItemSerializer(many=True)
    total_assets = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_liabilities = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_equity = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_passif_and_equity = serializers.DecimalField(max_digits=14, decimal_places=2)


class FinancialStatementsSerializer(serializers.Serializer):
    period = serializers.CharField(allow_null=True)
    cpc = CPCSerializer()
    bilan = BilanSerializer()
