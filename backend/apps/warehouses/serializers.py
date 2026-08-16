"""Serializers du module warehouses."""

from __future__ import annotations

from rest_framework import serializers

from apps.warehouses.models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "code",
            "name",
            "address",
            "city",
            "phone_number",
            "manager",
            "manager_name",
            "is_default",
            "created_at",
        ]
        read_only_fields = ["id", "code", "is_default", "created_at"]

    def get_manager_name(self, obj: Warehouse) -> str:
        if obj.manager is None:
            return ""
        return f"{obj.manager.first_name} {obj.manager.last_name}".strip()


class WarehouseCreateSerializer(serializers.ModelSerializer):
    is_default = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Warehouse
        fields = ["name", "address", "city", "phone_number", "manager", "is_default"]

    def validate_manager(self, value):  # noqa: ANN001, ANN201
        request = self.context.get("request")
        if (
            value is not None
            and request is not None
            and value.cooperative_id != request.user.cooperative_id
        ):
            raise serializers.ValidationError("Le responsable doit appartenir à votre coopérative.")
        return value
