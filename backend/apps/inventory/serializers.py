"""
Serializers du module inventory.

IMPORTANT : les endpoints d'action (stock-in/out/transfer) utilisent des
UUIDField simples pour product/warehouse plutôt que des
PrimaryKeyRelatedField(queryset=Model.objects.all()) déclarés en dur.

Pourquoi : un `queryset=Model.objects.all()` écrit directement dans le
corps d'une classe de serializer NON générée par ModelSerializer serait
évalué UNE SEULE FOIS à l'import du module (avant toute requête, donc
avant que le tenant ne soit résolu) — même piège que le bug corrigé à
l'Epic 4 sur les vues. La résolution de l'objet (et la vérification qu'il
appartient bien à la coopérative de l'utilisateur) se fait donc
explicitement dans la vue via get_object_or_404, jamais via la validation
automatique du serializer.
"""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.inventory.models import StockLevel, StockMovement, StockMovementReason


class StockLevelSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    unit_symbol = serializers.CharField(source="product.unit.symbol", read_only=True)
    is_below_threshold = serializers.SerializerMethodField()

    class Meta:
        model = StockLevel
        fields = [
            "id",
            "product",
            "product_sku",
            "warehouse",
            "warehouse_code",
            "quantity",
            "unit_symbol",
            "is_below_threshold",
            "updated_at",
        ]
        read_only_fields = fields

    def get_is_below_threshold(self, obj: StockLevel) -> bool:
        return obj.quantity < obj.product.minimum_stock_threshold


class StockMovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    destination_warehouse_code = serializers.CharField(
        source="destination_warehouse.code", read_only=True, default=None
    )
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "movement_type",
            "reason",
            "product",
            "product_sku",
            "warehouse",
            "warehouse_code",
            "destination_warehouse",
            "destination_warehouse_code",
            "quantity",
            "reference",
            "notes",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj: StockMovement) -> str:
        if obj.created_by is None:
            return ""
        return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()


class StockMovementInSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    warehouse_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=Decimal("0.001"))
    reason = serializers.ChoiceField(
        choices=StockMovementReason.choices, default=StockMovementReason.ADJUSTMENT
    )
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class StockMovementOutSerializer(StockMovementInSerializer):
    pass


class StockMovementTransferSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    from_warehouse_id = serializers.UUIDField()
    to_warehouse_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=Decimal("0.001"))
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
