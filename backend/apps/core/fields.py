"""
Champ traduisible réutilisable pour tout modèle nécessitant du contenu
multilingue saisi par l'utilisateur (nom de produit, catégorie, description...).

Stocké en JSONField : {"fr": "Huile d'argan", "ar": "زيت الأركان"}

Choix assumé : pas de django-modeltranslation (colonne par langue -> migrations
lourdes) ni django-parler (table séparée -> jointures coûteuses sur catalogue
volumineux). Un JSONField avec fallback applicatif est plus simple, plus
rapide, et prêt pour une 3e langue (anglais) sans migration.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TranslatedField(models.JSONField):
    """JSONField spécialisé, valide que seules les langues supportées sont présentes."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("default", dict)
        super().__init__(*args, **kwargs)

    def validate(self, value: dict, model_instance: Any) -> None:
        super().validate(value, model_instance)
        allowed = set(settings.SUPPORTED_LANGUAGES)
        invalid_keys = set(value.keys()) - allowed
        if invalid_keys:
            raise ValidationError(f"Langues non supportées : {invalid_keys}")


def get_translated_value(field_value: dict | None, lang: str) -> str:
    """
    Récupère la valeur traduite avec fallback :
    langue demandée -> langue par défaut -> première valeur disponible -> "".
    """
    if not field_value:
        return ""
    if lang in field_value and field_value[lang]:
        return field_value[lang]
    default_lang = settings.LANGUAGE_CODE
    if default_lang in field_value and field_value[default_lang]:
        return field_value[default_lang]
    return next(iter(field_value.values()), "")
