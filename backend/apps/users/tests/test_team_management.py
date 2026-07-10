"""
Tests de gestion d'équipe : changement de rôle, désactivation, garde-fous.
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


class TeamManagementTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")

        self.owner = User.objects.create_user(
            username="owner", email="owner@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="owner",
        )
        self.admin = User.objects.create_user(
            username="admin", email="admin@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="admin",
        )
        self.staff = User.objects.create_user(
            username="staff", email="staff@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="staff",
        )

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_owner_can_list_team(self) -> None:
        self._auth(self.owner)
        response = self.client.get(reverse("users:team-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]) if "results" in response.data else len(response.data), 3)

    def test_admin_can_promote_staff_to_admin(self) -> None:
        self._auth(self.admin)
        url = reverse("users:change-role", args=[self.staff.id])
        response = self.client.patch(url, {"role": "admin"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.role, "admin")

    def test_admin_cannot_promote_to_owner(self) -> None:
        self._auth(self.admin)
        url = reverse("users:change-role", args=[self.staff.id])
        response = self.client.patch(url, {"role": "owner"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_modify_owner_role(self) -> None:
        self._auth(self.admin)
        url = reverse("users:change-role", args=[self.owner.id])
        response = self.client.patch(url, {"role": "staff"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_change_own_role(self) -> None:
        self._auth(self.owner)
        url = reverse("users:change-role", args=[self.owner.id])
        response = self.client.patch(url, {"role": "admin"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_deactivate_last_owner(self) -> None:
        self._auth(self.admin)
        # admin tente de désactiver owner -> refusé car il est OWNER (règle séparée)
        url = reverse("users:deactivate", args=[self.owner.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_deactivate_admin(self) -> None:
        self._auth(self.owner)
        url = reverse("users:deactivate", args=[self.admin.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_active)

    def test_cannot_deactivate_self(self) -> None:
        self._auth(self.owner)
        url = reverse("users:deactivate", args=[self.owner.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_cannot_access_team_management_endpoints(self) -> None:
        self._auth(self.staff)
        url = reverse("users:deactivate", args=[self.admin.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_second_owner_can_be_deactivated_safely(self) -> None:
        second_owner = User.objects.create_user(
            username="owner2", email="owner2@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="owner",
        )
        self._auth(self.owner)
        url = reverse("users:deactivate", args=[second_owner.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
