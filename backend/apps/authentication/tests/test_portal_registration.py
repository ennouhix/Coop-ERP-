"""
Tests du parcours d'inscription portail : email de confirmation, activation
du compte, auto-login, garde-fous (jetons à usage unique, expiration, throttle).
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cooperatives.models import ActivationStatus, Cooperative, CooperativeActivation

User = get_user_model()

VALID_PAYLOAD = {
    "cooperative_name": "Coopérative Portail de Test",
    "owner_first_name": "Youssef",
    "owner_last_name": "Benali",
    "owner_email": "youssef@portail-test.ma",
    "owner_password": "MotDePasseSolide123",
}


class PortalRegistrationTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.register_url = reverse("authentication:register")
        self.verify_url = reverse("authentication:register-verify")
        self.login_url = reverse("authentication:login")

    def test_registration_creates_pending_owner_and_sends_email(self) -> None:
        response = self.client.post(self.register_url, VALID_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("access", response.data)
        self.assertEqual(response.data["email"], "youssef@portail-test.ma")

        owner = User.objects.get(email="youssef@portail-test.ma")
        self.assertFalse(owner.is_active, "Le compte reste inactif avant validation de l'email")
        self.assertEqual(owner.role, "owner")
        self.assertTrue(Cooperative.objects.filter(name=VALID_PAYLOAD["cooperative_name"]).exists())

        activation = CooperativeActivation.objects.get(user=owner)
        self.assertEqual(activation.status, ActivationStatus.PENDING)
        self.assertTrue(
            CooperativeActivation.objects.filter(cooperative=owner.cooperative).exists()
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("youssef@portail-test.ma", mail.outbox[0].to)
        self.assertIn("/activate-account?token=", mail.outbox[0].body)
        self.assertIn(activation.token, mail.outbox[0].body)

    def test_login_blocked_before_activation(self) -> None:
        self.client.post(self.register_url, VALID_PAYLOAD)

        response = self.client.post(
            self.login_url,
            {"email": "youssef@portail-test.ma", "password": "MotDePasseSolide123"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_activation_activates_account_and_returns_usable_tokens(self) -> None:
        self.client.post(self.register_url, VALID_PAYLOAD)
        activation = CooperativeActivation.objects.get(user__email="youssef@portail-test.ma")

        response = self.client.post(self.verify_url, {"token": activation.token})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "youssef@portail-test.ma")

        owner = User.objects.get(email="youssef@portail-test.ma")
        self.assertTrue(owner.is_active)

        activation.refresh_from_db()
        self.assertEqual(activation.status, ActivationStatus.USED)
        self.assertIsNotNone(activation.activated_at)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        me_response = self.client.get(reverse("authentication:me"))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], "youssef@portail-test.ma")

    def test_login_succeeds_after_activation(self) -> None:
        self.client.post(self.register_url, VALID_PAYLOAD)
        activation = CooperativeActivation.objects.get(user__email="youssef@portail-test.ma")
        self.client.post(self.verify_url, {"token": activation.token})

        response = self.client.post(
            self.login_url,
            {"email": "youssef@portail-test.ma", "password": "MotDePasseSolide123"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_activation_token_is_single_use(self) -> None:
        self.client.post(self.register_url, VALID_PAYLOAD)
        activation = CooperativeActivation.objects.get(user__email="youssef@portail-test.ma")

        self.client.post(self.verify_url, {"token": activation.token})
        second_attempt = self.client.post(self.verify_url, {"token": activation.token})
        self.assertEqual(second_attempt.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activation_rejects_unknown_token(self) -> None:
        response = self.client.post(self.verify_url, {"token": "jeton-qui-nexiste-pas"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "invalid_token")

    def test_activation_rejects_expired_token(self) -> None:
        self.client.post(self.register_url, VALID_PAYLOAD)
        activation = CooperativeActivation.objects.get(user__email="youssef@portail-test.ma")
        activation.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        activation.save(update_fields=["expires_at"])

        response = self.client.post(self.verify_url, {"token": activation.token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        owner = User.objects.get(email="youssef@portail-test.ma")
        self.assertFalse(owner.is_active)

    def test_registration_rejects_duplicate_email(self) -> None:
        self.client.post(self.register_url, VALID_PAYLOAD)
        cache.clear()  # évite que le throttle masque le vrai test (400 attendu, pas 429)

        duplicate = {**VALID_PAYLOAD, "cooperative_name": "Une Autre Coopérative"}
        response = self.client.post(self.register_url, duplicate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Cooperative.objects.count(), 1, "Aucune coopérative orpheline ne doit être créée"
        )

    def test_registration_rejects_weak_password(self) -> None:
        weak_payload = {**VALID_PAYLOAD, "owner_password": "123"}
        response = self.client.post(self.register_url, weak_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_is_rate_limited(self) -> None:
        for i in range(5):
            payload = {**VALID_PAYLOAD, "owner_email": f"user{i}@portail-test.ma"}
            self.client.post(self.register_url, payload)

        response = self.client.post(
            self.register_url, {**VALID_PAYLOAD, "owner_email": "user6@portail-test.ma"}
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
