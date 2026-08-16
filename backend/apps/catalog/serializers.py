"""
Serializers du catalogue.

Les champs TranslatedField (`name`, `description`) sont exposés en lecture
sous deux formes :
- `name` : objet brut {"fr": "...", "ar": "..."} pour l'édition côté frontend.
- `name_display` : valeur résolue selon la langue de la requête
  (header Accept-Language), pour l'affichage direct sans logique côté client.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.catalog.models import Category, Product, Unit
from apps.core.fields import get_translated_value


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "name", "symbol", "unit_type", "created_at"]
        read_only_fields = ["id", "created_at"]


class CategorySerializer(serializers.ModelSerializer):
    name_display = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "name_display", "parent", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_name_display(self, obj: Category) -> str:
        request = self.context.get("request")
        lang = getattr(request, "LANGUAGE_CODE", "fr") if request else "fr"
        return get_translated_value(obj.name, lang)

    def validate_parent(self, value: Category | None) -> Category | None:
        instance = getattr(self, "instance", None)
        if value is not None and instance is not None and value.pk == instance.pk:
            raise serializers.ValidationError(
                "Une catégorie ne peut pas être sa propre catégorie parente."
            )
        return value


class ProductSerializer(serializers.ModelSerializer):
    name_display = serializers.SerializerMethodField()
    category_name_display = serializers.SerializerMethodField()
    unit_symbol = serializers.CharField(source="unit.symbol", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "barcode",
            "name",
            "name_display",
            "category",
            "category_name_display",
            "unit",
            "unit_symbol",
            "reference_purchase_price",
            "reference_sale_price",
            "minimum_stock_threshold",
            "description",
            "is_sellable",
            "is_purchasable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "sku", "created_at", "updated_at"]

    def get_name_display(self, obj: Product) -> str:
        request = self.context.get("request")
        lang = getattr(request, "LANGUAGE_CODE", "fr") if request else "fr"
        return get_translated_value(obj.name, lang)

    def get_category_name_display(self, obj: Product) -> str:
        if obj.category is None:
            return ""
        request = self.context.get("request")
        lang = getattr(request, "LANGUAGE_CODE", "fr") if request else "fr"
        return get_translated_value(obj.category.name, lang)


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "barcode",
            "name",
            "category",
            "unit",
            "reference_purchase_price",
            "reference_sale_price",
            "minimum_stock_threshold",
            "description",
            "is_sellable",
            "is_purchasable",
        ]

    def validate_name(self, value: dict) -> dict:
        if not value or not value.get("fr"):
            raise serializers.ValidationError("Le nom en français est obligatoire.")
        return value

    def validate_barcode(self, value: str) -> str:
        if not value:
            return value
        request = self.context.get("request")
        cooperative_id = request.user.cooperative_id if request else None
        if Product.objects.filter(cooperative_id=cooperative_id, barcode=value).exists():
            raise serializers.ValidationError(
                "Un produit avec ce code-barres existe déjà dans votre coopérative."
            )
        return value
