"""
Serializers du module cooperatives.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.cooperatives.models import Cooperative

User = get_user_model()


class CooperativeRegistrationSerializer(serializers.Serializer):
    """
    Formulaire d'inscription self-service : nom de la coopérative +
    informations du premier utilisateur (futur OWNER).
    Pas de ModelSerializer ici car les données couvrent deux modèles
    (Cooperative + User), assemblés par apps.cooperatives.services.
    """

    cooperative_name = serializers.CharField(max_length=255, min_length=2)
    owner_first_name = serializers.CharField(max_length=150)
    owner_last_name = serializers.CharField(max_length=150)
    owner_email = serializers.EmailField()
    owner_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_owner_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value.lower()


class CooperativeSerializer(serializers.ModelSerializer):
    """Lecture complète des informations de la coopérative (endpoint /me)."""

    is_trial_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cooperative
        fields = [
            "id", "name", "slug", "logo",
            "legal_name", "ice", "rc_number",
            "email", "phone_number", "address", "city", "region",
            "default_language",
            "subscription_plan", "subscription_status", "trial_ends_at", "is_trial_expired",
            "created_at",
        ]
        read_only_fields = [
            "id", "slug", "subscription_plan", "subscription_status",
            "trial_ends_at", "is_trial_expired", "created_at",
        ]


class CooperativeUpdateSerializer(serializers.ModelSerializer):
    """
    Mise à jour des informations modifiables par un OWNER/ADMIN. Le slug,
    le statut d'abonnement et le plan sont volontairement exclus : ce ne
    sont pas des champs que l'utilisateur pilote lui-même (le slug est
    immuable, l'abonnement sera géré par un futur module de facturation
    plateforme).
    """

    class Meta:
        model = Cooperative
        fields = [
            "name", "legal_name", "ice", "rc_number",
            "email", "phone_number", "address", "city", "region",
            "default_language",
        ]


class CooperativeLogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cooperative
        fields = ["logo"]
