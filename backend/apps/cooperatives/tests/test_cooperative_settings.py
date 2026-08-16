"""
Tests de gestion des informations de la coopérative (/me).
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.cooperatives.models import Cooperative

User = get_user_model()


class CooperativeSettingsTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")

        self.owner = User.objects.create_user(
            username="owner",
            email="owner@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="owner",
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="staff",
        )

        other_coop = Cooperative.objects.create(name="Autre Coopérative", slug="autre")
        self.foreign_owner = User.objects.create_user(
            username="foreign",
            email="foreign@autre.ma",
            password="MotDePasseSolide123",
            cooperative=other_coop,
            role="owner",
        )

        self.me_url = reverse("cooperatives:me")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_any_member_can_view_cooperative(self) -> None:
        self._auth(self.staff)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Coopérative Argane")

    def test_owner_can_update_cooperative(self) -> None:
        self._auth(self.owner)
        response = self.client.patch(
            self.me_url, {"legal_name": "Argane SARL", "ice": "001234567000012"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cooperative.refresh_from_db()
        self.assertEqual(self.cooperative.legal_name, "Argane SARL")
        self.assertEqual(self.cooperative.ice, "001234567000012")

    def test_staff_cannot_update_cooperative(self) -> None:
        self._auth(self.staff)
        response = self.client.patch(self.me_url, {"legal_name": "Tentative Non Autorisée"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_ice_format_is_rejected(self) -> None:
        self._auth(self.owner)
        response = self.client.patch(self.me_url, {"ice": "123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_slug_cannot_be_modified(self) -> None:
        self._auth(self.owner)
        response = self.client.patch(self.me_url, {"slug": "nouveau-slug"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cooperative.refresh_from_db()
        self.assertEqual(self.cooperative.slug, "argane")  # inchangé, champ ignoré côté serializer

    def test_user_only_sees_own_cooperative(self) -> None:
        """Un utilisateur d'une autre coopérative ne doit jamais voir les données d'Argane."""
        self._auth(self.foreign_owner)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Autre Coopérative")

    def test_unauthenticated_access_is_rejected(self) -> None:
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
