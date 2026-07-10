"""Serializers du module members."""
from __future__ import annotations

from rest_framework import serializers

from apps.members.models import Member


class MemberSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Member
        fields = [
            "id", "member_number", "member_type",
            "first_name", "last_name", "full_name",
            "cin", "phone_number", "email", "address", "city",
            "birth_date", "join_date", "status", "shares_count", "notes",
            "created_at", "updated_at",
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
            "member_type", "first_name", "last_name",
            "cin", "phone_number", "email", "address", "city",
            "birth_date", "join_date", "shares_count", "notes",
        ]

    def validate_cin(self, value: str) -> str:
        if not value:
            return value
        request = self.context.get("request")
        cooperative_id = request.user.cooperative_id if request else None
        if Member.objects.filter(cooperative_id=cooperative_id, cin=value).exists():
            raise serializers.ValidationError("Un membre avec cette CIN existe déjà dans votre coopérative.")
        return value
