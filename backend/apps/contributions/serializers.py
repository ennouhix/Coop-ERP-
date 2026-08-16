"""Serializers du module contributions."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.contributions.models import Contribution, ContributionStatus


def _product_name_fr(contribution: Contribution) -> str:
    from apps.core.fields import get_translated_value

    return get_translated_value(contribution.product.name, "fr") or contribution.product.sku


class ContributionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    product_name = serializers.SerializerMethodField()
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Contribution
        fields = [
            "id",
            "member",
            "member_name",
            "product",
            "product_name",
            "product_sku",
            "quantity",
            "unit_price",
            "total_amount",
            "contribution_date",
            "campaign",
            "status",
            "payment_date",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_product_name(self, obj: Contribution) -> str:
        return _product_name_fr(obj)


class ContributionCreateSerializer(serializers.Serializer):
    """
    Création d'un apport. `member_id` et `product_id` sont de simples UUID
    résolus dans la vue au sein de la coopérative de l'utilisateur (règle
    du module inventory : jamais de queryset évaluée à l'import).
    """

    member_id = serializers.UUIDField()
    product_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=Decimal("0.001"))
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    contribution_date = serializers.DateField(required=False)
    campaign = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(
        choices=ContributionStatus.choices, default=ContributionStatus.PENDING, required=False
    )
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
