"""
Serializers du module users (gestion d'équipe et invitations).
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.authentication.models import UserRole
from apps.users.models import Invitation

User = get_user_model()


class TeamMemberSerializer(serializers.ModelSerializer):
    """Représentation d'un membre de l'équipe (endpoint de listing)."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "is_active",
            "date_joined",
        ]
        read_only_fields = fields


class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRole.choices)


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.STAFF)


class InvitationSerializer(serializers.ModelSerializer):
    invited_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = ["id", "email", "role", "status", "expires_at", "created_at", "invited_by_name"]
        read_only_fields = fields

    def get_invited_by_name(self, obj: Invitation) -> str:
        if obj.invited_by is None:
            return ""
        return f"{obj.invited_by.first_name} {obj.invited_by.last_name}".strip()


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, validators=[validate_password])
