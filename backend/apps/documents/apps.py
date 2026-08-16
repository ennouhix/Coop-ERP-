"""
App `documents` (M16) — documents commerciaux PDF et leur personnalisation.

Génère les bons de livraison, bons de commande et bons de réception en PDF,
permet de personnaliser chaque type de document par coopérative (en-tête,
pied, conditions, couleur d'accent, logo) via `DocumentTemplate`, et archive
les documents générés dans `DocumentArchive` pour re-téléchargement ultérieur.
"""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents"
    verbose_name = "Documents commerciaux"
