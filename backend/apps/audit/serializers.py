"""Serializer du journal d'activité — lecture seule, ledger immuable."""

from __future__ import annotations

from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    actor_email = serializers.CharField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor_name",
            "actor_email",
            "action",
            "target_type",
            "target_id",
            "target_repr",
            "metadata",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj: AuditLog) -> str:
        if obj.actor is None:
            return "Système"
        return f"{obj.actor.first_name} {obj.actor.last_name}".strip() or obj.actor.email
