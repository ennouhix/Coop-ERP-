"""
Serializers du module authentification.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.authentication.models import UserRole

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Étend le serializer JWT standard pour :
    1. Refuser explicitement un compte désactivé (RG-1) avec un message clair
    2. Embarquer cooperative_id et role dans les claims du token (RG-2),
       ce qui évite un appel API supplémentaire au frontend pour connaître
       le contexte utilisateur, et c'est cette claim que TenantMiddleware lit.
    """

    @classmethod
    def get_token(cls, user: User) -> Any:  # type: ignore[override]
        token = super().get_token(user)
        token["cooperative_id"] = str(user.cooperative_id) if user.cooperative_id else None
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        if not self.user.is_active:
            raise serializers.ValidationError(
                "Ce compte est désactivé. Contactez votre administrateur.",
                code="account_disabled",
            )
        data["user"] = UserProfileSerializer(self.user).data
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Représentation du profil utilisateur exposée par /me et dans la réponse de login.
    `modules` = modules métier effectivement accessibles à l'utilisateur (matrice
    RBAC + surcharges de sa coopérative), utilisés par le frontend pour afficher
    ou masquer les entrées du sidebar.
    """

    cooperative_id = serializers.UUIDField(read_only=True)
    modules = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "cooperative_id",
            "is_active",
            "date_joined",
            "modules",
        ]
        read_only_fields = ["id", "role", "cooperative_id", "is_active", "date_joined", "modules"]

    def get_modules(self, obj: User) -> list[str]:
        if obj.role == UserRole.OWNER:
            from apps.roles_permissions.matrix import MODULES

            return list(MODULES)
        if not obj.cooperative_id:
            return []
        from apps.roles_permissions.services import effective_modules_for_role

        return sorted(effective_modules_for_role(cooperative_id=obj.cooperative_id, role=obj.role))


class ChangePasswordSerializer(serializers.Serializer):
    """
    Changement de mot de passe pour l'utilisateur authentifié.
    Nécessite l'ancien mot de passe (évite qu'une session volée mais encore
    active permette de verrouiller le vrai propriétaire du compte hors de
    son compte en changeant le mot de passe sans le connaître).
    """

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value

    def validate_new_password(self, value: str) -> str:
        validate_password(value, user=self.context["request"].user)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Ne valide QUE le format de l'email, jamais son existence en base :
    révéler l'existence d'un compte via une erreur de validation
    permettrait l'énumération des utilisateurs enregistrés.
    """

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value
