"""
Tests du flux de réinitialisation de mot de passe.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cooperatives.models import Cooperative

User = get_user_model()


class PasswordResetTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")
        self.user = User.objects.create_user(
            username="fatima",
            email="fatima@example.com",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="owner",
        )
        self.request_url = reverse("authentication:password-reset-request")
        self.confirm_url = reverse("authentication:password-reset-confirm")
        self.login_url = reverse("authentication:login")

    def test_reset_request_for_existing_email_sends_mail(self) -> None:
        response = self.client.post(self.request_url, {"email": "fatima@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("fatima@example.com", mail.outbox[0].to)

    def test_reset_request_for_unknown_email_still_returns_200(self) -> None:
        """Anti-énumération : la réponse ne doit jamais varier selon l'existence du compte."""
        response = self.client.post(self.request_url, {"email": "inconnu@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_with_valid_token_changes_password(self) -> None:
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = PasswordResetTokenGenerator().make_token(self.user)

        response = self.client.post(
            self.confirm_url,
            {"uid": uid, "token": token, "new_password": "NouveauMdpSolide456"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        login = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "NouveauMdpSolide456"}
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_confirm_with_invalid_token_is_rejected(self) -> None:
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(
            self.confirm_url,
            {"uid": uid, "token": "token-invalide", "new_password": "NouveauMdpSolide456"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_token_cannot_be_reused(self) -> None:
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = PasswordResetTokenGenerator().make_token(self.user)

        first = self.client.post(
            self.confirm_url,
            {"uid": uid, "token": token, "new_password": "NouveauMdpSolide456"},
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)

        second = self.client.post(
            self.confirm_url,
            {"uid": uid, "token": token, "new_password": "EncoreUnAutreMdp789"},
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
