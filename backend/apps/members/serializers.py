"""Serializers du module members."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.members.models import Member, ShareTransaction, ShareTransactionType


class MemberSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "member_number",
            "member_type",
            "first_name",
            "last_name",
            "full_name",
            "cin",
            "phone_number",
            "email",
            "address",
            "city",
            "birth_date",
            "join_date",
            "status",
            "shares_count",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "member_number", "created_at", "updated_at"]


class MemberCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de création : n'inclut PAS member_number (généré côté
    service), ni cooperative (déduite de l'utilisateur connecté).

    Nécessite `context={"request": request}` pour valider l'unicité de la
    CIN au sein de la coopérative de l'utilisateur connecté.
    """

    class Meta:
        model = Member
        fields = [
            "member_type",
            "first_name",
            "last_name",
            "cin",
            "phone_number",
            "email",
            "address",
            "city",
            "birth_date",
            "join_date",
            "shares_count",
            "notes",
        ]

    def validate_cin(self, value: str) -> str:
        if not value:
            return value
        request = self.context.get("request")
        cooperative_id = request.user.cooperative_id if request else None
        if Member.objects.filter(cooperative_id=cooperative_id, cin=value).exists():
            raise serializers.ValidationError(
                "Un membre avec cette CIN existe déjà dans votre coopérative."
            )
        return value


class ShareTransactionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = ShareTransaction
        fields = [
            "id",
            "member",
            "member_name",
            "transaction_type",
            "shares_count",
            "amount_per_share",
            "total_amount",
            "transaction_date",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ShareTransactionCreateSerializer(serializers.Serializer):
    """
    Création d'un mouvement de parts.

    `member_id` est un simple UUID : l'objet Member est résolu dans la vue
    via get_object_or_404 au sein de la coopérative de l'utilisateur (même
    règle que le module inventory — jamais de queryset évaluée à l'import).
    """

    member_id = serializers.UUIDField()
    transaction_type = serializers.ChoiceField(choices=ShareTransactionType.choices)
    shares_count = serializers.IntegerField(min_value=1)
    amount_per_share = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    transaction_date = serializers.DateField(required=False)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
