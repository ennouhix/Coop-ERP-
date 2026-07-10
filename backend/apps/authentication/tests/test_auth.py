"""
Tests du module authentification.

Couvre : login réussi/échoué, claims JWT, throttle anti brute-force,
refresh token, logout + blacklist, endpoint /me, changement de mot de passe
et son effet sur les tokens existants.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cooperatives.models import Cooperative

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()  # évite qu'un throttle déclenché par un test précédent fausse celui-ci
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")
        self.user = User.objects.create_user(
            username="fatima",
            email="fatima@example.com",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="owner",
        )
        self.login_url = reverse("authentication:login")
        self.refresh_url = reverse("authentication:refresh")
        self.logout_url = reverse("authentication:logout")
        self.me_url = reverse("authentication:me")
        self.change_password_url = reverse("authentication:change-password")

    def test_login_success_returns_tokens_and_claims(self) -> None:
        response = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "MotDePasseSolide123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "fatima@example.com")

    def test_login_wrong_password_fails(self) -> None:
        response = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "mauvais_mdp"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_disabled_account_is_rejected(self) -> None:
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "MotDePasseSolide123"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_throttled_after_repeated_failures(self) -> None:
        for _ in range(5):
            self.client.post(self.login_url, {"email": "fatima@example.com", "password": "faux"})

        response = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "faux"}
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_refresh_token_issues_new_access_token(self) -> None:
        login = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "MotDePasseSolide123"}
        )
        response = self.client.post(self.refresh_url, {"refresh": login.data["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_blacklists_refresh_token(self) -> None:
        login = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "MotDePasseSolide123"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        logout_response = self.client.post(self.logout_url, {"refresh": login.data["refresh"]})
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)

        # Le refresh token blacklisté ne doit plus jamais fonctionner.
        retry = self.client.post(self.refresh_url, {"refresh": login.data["refresh"]})
        self.assertEqual(retry.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_requires_authentication(self) -> None:
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_returns_own_profile(self) -> None:
        login = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "MotDePasseSolide123"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "fatima@example.com")
        self.assertEqual(response.data["cooperative_id"], str(self.cooperative.id))

    def test_change_password_requires_correct_old_password(self) -> None:
        login = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "MotDePasseSolide123"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.post(
            self.change_password_url,
            {"old_password": "faux_mdp", "new_password": "NouveauMdpSolide456"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_success_blacklists_existing_tokens(self) -> None:
        login = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "MotDePasseSolide123"}
        )
        old_refresh = login.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = self.client.post(
            self.change_password_url,
            {"old_password": "MotDePasseSolide123", "new_password": "NouveauMdpSolide456"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # L'ancien refresh token, émis avant le changement, doit être révoqué.
        retry = self.client.post(self.refresh_url, {"refresh": old_refresh})
        self.assertEqual(retry.status_code, status.HTTP_401_UNAUTHORIZED)

        # Le nouveau mot de passe doit permettre une connexion normale.
        new_login = self.client.post(
            self.login_url, {"email": "fatima@example.com", "password": "NouveauMdpSolide456"}
        )
        self.assertEqual(new_login.status_code, status.HTTP_200_OK)
