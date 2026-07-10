"""Validateurs métier pour le module members."""
from __future__ import annotations

from django.core.validators import RegexValidator

cin_validator = RegexValidator(
    regex=r"^[A-Za-z]{1,2}\d{1,6}$",
    message="Format de CIN invalide (ex: AB123456).",
)

phone_validator = RegexValidator(
    regex=r"^\+?\d{9,15}$",
    message="Numéro de téléphone invalide (9 à 15 chiffres, +indicatif optionnel).",
)
