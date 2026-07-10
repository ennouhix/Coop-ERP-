"""Serializers du module partners."""
from __future__ import annotations

from rest_framework import serializers

from apps.partners.models import Partner


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = [
            "id", "code", "is_customer", "is_supplier",
            "partner_kind", "name", "ice",
            "phone_number", "email", "address", "city",
            "payment_terms_days", "credit_limit",
            "status", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "code", "created_at", "updated_at"]


class PartnerCreateSerializer(serializers.ModelSerializer):
    """
    N'inclut pas `code` (généré par le service) ni `cooperative` (déduite
    de l'utilisateur connecté). La règle "au moins client ou fournisseur"
    est appliquée par Partner.clean() côté service, pas dupliquée ici.
    """

    class Meta:
        model = Partner
        fields = [
            "is_customer", "is_supplier",
            "partner_kind", "name", "ice",
            "phone_number", "email", "address", "city",
            "payment_terms_days", "credit_limit", "notes",
        ]
