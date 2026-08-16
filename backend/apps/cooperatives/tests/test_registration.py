"""
Tests d'inscription self-service d'une coopérative.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cooperatives.models import Cooperative

User = get_user_model()

VALID_PAYLOAD = {
    "cooperative_name": "Coopérative Argane du Sud",
    "owner_first_name": "Fatima",
    "owner_last_name": "El Amrani",
    "owner_email": "fatima@argane-sud.ma",
    "owner_password": "MotDePasseSolide123",
}


class CooperativeRegistrationTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.register_url = reverse("cooperatives:register")

    def test_registration_creates_cooperative_and_owner(self) -> None:
        response = self.client.post(self.register_url, VALID_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Cooperative.objects.filter(name=VALID_PAYLOAD["cooperative_name"]).exists())
        owner = User.objects.get(email="fatima@argane-sud.ma")
        self.assertEqual(owner.role, "owner")
        self.assertEqual(owner.cooperative.name, VALID_PAYLOAD["cooperative_name"])

    def test_registration_returns_usable_tokens(self) -> None:
        response = self.client.post(self.register_url, VALID_PAYLOAD)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Le token retourné doit permettre d'accéder immédiatement à /me sans re-login.
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        me_response = self.client.get(reverse("authentication:me"))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "fatima@argane-sud.ma")

    def test_registration_generates_unique_slug_on_name_collision(self) -> None:
        self.client.post(self.register_url, VALID_PAYLOAD)

        second_payload = {**VALID_PAYLOAD, "owner_email": "autre@argane-sud.ma"}
        response = self.client.post(self.register_url, second_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        slugs = list(Cooperative.objects.values_list("slug", flat=True))
        self.assertEqual(len(slugs), len(set(slugs)), "Les slugs générés doivent être uniques")

    def test_registration_rejects_duplicate_email(self) -> None:
        self.client.post(self.register_url, VALID_PAYLOAD)
        cache.clear()  # évite que le throttle masque le vrai test (409 attendu, pas 429)

        duplicate = {**VALID_PAYLOAD, "cooperative_name": "Une Autre Coopérative"}
        response = self.client.post(self.register_url, duplicate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_rejects_weak_password(self) -> None:
        weak_payload = {**VALID_PAYLOAD, "owner_password": "123"}
        response = self.client.post(self.register_url, weak_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_is_rate_limited(self) -> None:
        for i in range(5):
            payload = {**VALID_PAYLOAD, "owner_email": f"user{i}@test.ma"}
            self.client.post(self.register_url, payload)

        response = self.client.post(
            self.register_url, {**VALID_PAYLOAD, "owner_email": "user6@test.ma"}
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_atomicity_no_orphan_cooperative_on_duplicate_email(self) -> None:
        """
        Si la création échoue (ex: doublon détecté malgré tout), aucune
        coopérative orpheline sans propriétaire ne doit rester en base.
        """
        self.client.post(self.register_url, VALID_PAYLOAD)
        cache.clear()
        count_before = Cooperative.objects.count()

        duplicate = {**VALID_PAYLOAD, "cooperative_name": "Coopérative Fantôme"}
        self.client.post(self.register_url, duplicate)

        self.assertEqual(Cooperative.objects.count(), count_before)
        self.assertFalse(Cooperative.objects.filter(name="Coopérative Fantôme").exists())
