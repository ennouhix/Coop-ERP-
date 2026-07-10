"""
Test d'introspection critique : empêche qu'un futur modèle métier soit ajouté
SANS hériter de TenantBaseModel, ce qui créerait une fuite de données entre
coopératives. Ce test doit rester vert en permanence — s'il échoue, c'est
qu'un modèle vient d'être ajouté sans isolation tenant et NE DOIT PAS être
mergé tel quel.
"""
from __future__ import annotations

from django.apps import apps
from django.test import TestCase

from apps.core.models import TenantBaseModel

# Modèles explicitement exemptés d'isolation tenant (données globales/système).
EXEMPT_MODELS = {
    "authentication.User",
    "cooperatives.Cooperative",
}


class TenantIsolationTestCase(TestCase):
    def test_all_business_models_are_tenant_scoped(self) -> None:
        offending: list[str] = []

        for model in apps.get_models():
            label = f"{model._meta.app_label}.{model.__name__}"

            if label in EXEMPT_MODELS:
                continue
            if model._meta.app_label in {"admin", "auth", "contenttypes", "sessions", "token_blacklist"}:
                continue
            if model.__module__.startswith("django."):
                continue

            if not issubclass(model, TenantBaseModel):
                offending.append(label)

        self.assertEqual(
            offending,
            [],
            f"Ces modèles n'héritent pas de TenantBaseModel et créent un "
            f"risque de fuite de données inter-tenant : {offending}",
        )
