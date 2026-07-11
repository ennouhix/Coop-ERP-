"""
Modèles du catalogue : unités de mesure, catégories hiérarchiques, produits.

Product.name et Category.name utilisent TranslatedField (apps.core.fields),
conçu à l'Epic 0 pour le contenu bilingue FR/AR saisi par l'utilisateur.
"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.fields import TranslatedField
from apps.core.models import TenantBaseModel


class UnitType(models.TextChoices):
    WEIGHT = "weight", "Poids"
    VOLUME = "volume", "Volume"
    COUNT = "count", "Unité (pièce)"
    LENGTH = "length", "Longueur"


class Unit(TenantBaseModel):
    """
    Unité de mesure (kg, litre, pièce...). Pas de conversion inter-unités
    en V1 : un produit a UNE unité de référence. Évolution future
    documentée en fin d'Epic (table de coefficients de conversion).
    """

    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, help_text="Ex: kg, L, pc")
    unit_type = models.CharField(max_length=10, choices=UnitType.choices, default=UnitType.COUNT)

    class Meta:
        verbose_name = "Unité"
        verbose_name_plural = "Unités"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["cooperative", "symbol"], name="unique_unit_symbol_per_cooperative"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.symbol})"


class Category(TenantBaseModel):
    """Catégorie de produit, éventuellement hiérarchique (auto-référence sur parent)."""

    name = TranslatedField(help_text='Ex: {"fr": "Huiles", "ar": "الزيوت"}')
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        indexes = [models.Index(fields=["cooperative", "parent"])]

    def __str__(self) -> str:
        from apps.core.fields import get_translated_value

        return get_translated_value(self.name, "fr") or str(self.pk)

    def clean(self) -> None:
        super().clean()
        if self.parent_id is None:
            return
        if self.parent_id == self.pk:
            raise ValidationError("Une catégorie ne peut pas être sa propre catégorie parente.")

        # Remonte la chaîne des parents pour détecter un cycle (ex: A -> B -> A).
        ancestor = self.parent
        visited = {self.pk} if self.pk else set()
        while ancestor is not None:
            if ancestor.pk in visited:
                raise ValidationError("Cette hiérarchie de catégories créerait une boucle.")
            visited.add(ancestor.pk)
            ancestor = ancestor.parent


class Product(TenantBaseModel):
    """Fiche produit du catalogue."""

    sku = models.CharField("SKU", max_length=20, db_index=True, editable=False)
    barcode = models.CharField(max_length=50, blank=True)

    name = TranslatedField(help_text='Ex: {"fr": "Huile d\'argane", "ar": "زيت الأركان"}')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="products")

    reference_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reference_sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    minimum_stock_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Seuil utilisé par le module Stock (Epic 8) pour déclencher une alerte.",
    )

    description = TranslatedField(blank=True)
    is_sellable = models.BooleanField(default=True)
    is_purchasable = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["sku"]
        constraints = [
            models.UniqueConstraint(fields=["cooperative", "sku"], name="unique_product_sku_per_cooperative"),
            models.UniqueConstraint(
                fields=["cooperative", "barcode"],
                condition=~models.Q(barcode=""),
                name="unique_product_barcode_per_cooperative",
            ),
        ]
        indexes = [models.Index(fields=["cooperative", "category"])]

    def __str__(self) -> str:
        from apps.core.fields import get_translated_value

        return f"{self.sku} — {get_translated_value(self.name, 'fr')}"
