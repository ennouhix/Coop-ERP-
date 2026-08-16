"""
Serializers du module cooperatives.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.cooperatives.models import Cooperative, CooperativeEmailConfig, EmailNotification

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


class ActivationSerializer(serializers.Serializer):
    """Jeton reçu par email, transmis au point de terminaison de vérification."""

    token = serializers.CharField(max_length=64)


class CooperativeSerializer(serializers.ModelSerializer):
    """Lecture complète des informations de la coopérative (endpoint /me)."""

    is_trial_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cooperative
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "legal_name",
            "ice",
            "rc_number",
            "email",
            "phone_number",
            "address",
            "city",
            "region",
            "default_language",
            "subscription_plan",
            "subscription_status",
            "trial_ends_at",
            "is_trial_expired",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "subscription_plan",
            "subscription_status",
            "trial_ends_at",
            "is_trial_expired",
            "created_at",
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
            "name",
            "legal_name",
            "ice",
            "rc_number",
            "email",
            "phone_number",
            "address",
            "city",
            "region",
            "default_language",
        ]


class CooperativeLogoSerializer(serializers.ModelSerializer):
    """Upload et validation du logo de la coopérative."""

    MAX_LOGO_SIZE_MB = 5

    class Meta:
        model = Cooperative
        fields = ["logo"]

    def validate_logo(self, value: object) -> object:
        if value is None:
            return value
        if hasattr(value, "size") and value.size > self.MAX_LOGO_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"Le fichier est trop volumineux ({self.MAX_LOGO_SIZE_MB} Mo max)."
            )
        if hasattr(value, "content_type") and not value.content_type.startswith("image/"):
            raise serializers.ValidationError("Seuls les fichiers image sont acceptés.")
        return value


class CooperativeEmailConfigSerializer(serializers.ModelSerializer):
    """
    Lecture et mise à jour de la configuration SMTP d'une coopérative.

    Le mot de passe est masqué en lecture (jamais renvoyé tel quel).
    Un champ `test_connection` permet de tester la config sans la sauvegarder.
    """

    test_connection = serializers.SerializerMethodField()

    class Meta:
        model = CooperativeEmailConfig
        fields = [
            "id",
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_use_tls",
            "from_name",
            "from_email",
            "is_configured",
            "test_connection",
        ]
        read_only_fields = ["id", "test_connection"]
        extra_kwargs = {
            "smtp_password": {"write_only": True},
        }

    def get_test_connection(self, obj: CooperativeEmailConfig) -> bool | None:
        """Indique si la config a déjà été testée avec succès."""
        if not obj.smtp_host:
            return None
        return None

    def validate(self, data: dict) -> dict:
        if data.get("is_configured"):
            for field in ("smtp_host", "smtp_port", "from_email"):
                if not data.get(field):
                    raise serializers.ValidationError(
                        {field: "Ce champ est requis lorsque la configuration est active."}
                    )
        return data


class EmailNotificationSerializer(serializers.ModelSerializer):
    """Lecture du journal des emails envoyés."""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = EmailNotification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "recipient_email",
            "recipient_name",
            "subject",
            "status",
            "status_display",
            "error_message",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
