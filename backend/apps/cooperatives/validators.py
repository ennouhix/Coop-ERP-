"""
Validateurs pour les identifiants légaux marocains.
"""

from __future__ import annotations

from django.core.validators import RegexValidator

ice_validator = RegexValidator(
    regex=r"^\d{15}$",
    message="L'ICE doit être composé exactement de 15 chiffres.",
)

phone_validator = RegexValidator(
    regex=r"^\+?\d{9,15}$",
    message="Numéro de téléphone invalide (9 à 15 chiffres, +indicatif optionnel).",
)
