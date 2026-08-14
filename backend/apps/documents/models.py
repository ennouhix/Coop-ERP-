"""
Modèles du module documents (M16).

- `DocumentTemplate` : personnalisation d'un type de document (bon de
  livraison, bon de commande, bon de réception) pour une coopérative.
  L'absence d'enregistrement = valeurs par défaut (aucune surcharge).
- `DocumentArchive` : copie PDF d'un document généré, conservée pour
  re-téléchargement même si la source évolue. Immuable en pratique : une
  seule archive par (coopérative, type, document source), régénérée au besoin.
"""
from __future__ import annotations

import uuid

from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import TenantBaseModel

accent_color_validator = RegexValidator(
    regex=r"^#[0-9a-fA-F]{6}$",
    message="La couleur d'accent doit être un code hexadécimal (#RRGGBB).",
)


class DocumentTemplateType(models.TextChoices):
    DELIVERY_NOTE = "delivery_note", "Bon de livraison"
    PURCHASE_ORDER = "purchase_order", "Bon de commande"
    RECEIPT = "receipt", "Bon de réception"


class DocumentSourceType(models.TextChoices):
    SALES_ORDER = "sales_order", "Commande de vente"
    PURCHASE_ORDER = "purchase_order", "Commande d'achat"


class DocumentTemplate(TenantBaseModel):
    """Personnalisation d'un type de document pour une coopérative."""

    template_type = models.CharField(max_length=30, choices=DocumentTemplateType.choices)
    header_text = models.TextField(
        blank=True, help_text="Texte affiché sous la raison sociale dans l'en-tête."
    )
    footer_text = models.TextField(
        blank=True, help_text="Ligne(s) ajoutée(s) dans le pied de page (coordonnées, mentions...)."
    )
    terms_text = models.TextField(
        blank=True, help_text="Conditions générales / remarques affichées sous le document."
    )
    accent_color = models.CharField(
        max_length=7, blank=True, validators=[accent_color_validator],
        help_text="Couleur d'accent du document (#RRGGBB). Vide = couleur par défaut.",
    )
    show_logo = models.BooleanField(
        default=True, help_text="Afficher le logo de la coopérative dans l'en-tête."
    )

    class Meta:
        verbose_name = "Modèle de document"
        verbose_name_plural = "Modèles de documents"
        ordering = ["template_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "template_type"],
                name="unique_template_type_per_cooperative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_template_type_display()} — {self.cooperative.name}"


class DocumentArchive(TenantBaseModel):
    """Copie PDF archivée d'un document généré (bon de livraison, etc.)."""

    doc_type = models.CharField(max_length=30, choices=DocumentTemplateType.choices)
    source_type = models.CharField(max_length=30, choices=DocumentSourceType.choices)
    source_id = models.UUIDField(editable=False, db_index=True)
    source_number = models.CharField(max_length=50, editable=False, db_index=True)
    pdf_file = models.FileField(upload_to="documents/")
    filename = models.CharField(max_length=255, editable=False)

    class Meta:
        verbose_name = "Document archivé"
        verbose_name_plural = "Documents archivés"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "doc_type", "source_id"],
                name="unique_archive_per_source_and_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_doc_type_display()} {self.source_number}"


def is_valid_source_id(value: object) -> bool:
    """Vrai si la valeur est un UUID valide (garde-fou des endpoints publics)."""
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return False
    return True
