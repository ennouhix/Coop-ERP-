"""
Tests des permissions par rôle modulables depuis le panneau d'administration :
surcharges par coopérative, isolation tenant, et règles de garde.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.cooperatives.models import Cooperative
from apps.roles_permissions.services import has_permission_for_cooperative

User = get_user_model()


class RolePermissionsTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Atlas", slug="atlas")

        self.owner = User.objects.create_user(
            username="owner",
            email="owner@atlas.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="owner",
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@atlas.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="admin",
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@atlas.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="staff",
        )

        self.url = reverse("roles_permissions:role-permissions")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _default_staff_modules(self) -> set[str]:
        from apps.roles_permissions.matrix import default_modules_for_role

        return default_modules_for_role("staff")

    # ---- Règles par défaut (matrice statique) ----

    def test_default_matrix_applies_without_overrides(self) -> None:
        self.assertTrue(
            has_permission_for_cooperative(
                cooperative_id=self.cooperative.id, role="staff", code="catalog.view"
            )
        )
        self.assertFalse(
            has_permission_for_cooperative(
                cooperative_id=self.cooperative.id, role="staff", code="catalog.edit"
            )
        )
        self.assertFalse(
            has_permission_for_cooperative(
                cooperative_id=self.cooperative.id, role="staff", code="accounting.view"
            )
        )
        self.assertTrue(
            has_permission_for_cooperative(
                cooperative_id=self.cooperative.id, role="accountant", code="accounting.post"
            )
        )

    def test_owner_has_everything(self) -> None:
        for code in ("accounting.post", "audit.view", "users.deactivate", "reports.view"):
            self.assertTrue(
                has_permission_for_cooperative(
                    cooperative_id=self.cooperative.id, role="owner", code=code
                )
            )

    def test_staff_cannot_access_accounting_by_default(self) -> None:
        self._auth(self.staff)
        response = self.client.get("/api/v1/accounting/accounts/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Accès au panneau d'administration ----

    def test_staff_cannot_manage_permissions(self) -> None:
        self._auth(self.staff)
        response = self.client.put(self.url, {"staff": ["accounting"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_read_permissions(self) -> None:
        self._auth(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("modules", response.data)
        self.assertIn("staff", response.data["roles"])

    # ---- Personnalisation des accès ----

    def test_admin_can_grant_staff_accounting_module(self) -> None:
        self._auth(self.admin)
        desired = sorted(self._default_staff_modules() | {"accounting"})
        response = self.client.put(self.url, {"staff": desired}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data["roles"]["staff"]), set(desired))

        # L'accès est effectif immédiatement sur les vues métier.
        self._auth(self.staff)
        response = self.client.get("/api/v1/accounting/accounts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_grant_only_accounting_revokes_other_modules(self) -> None:
        self._auth(self.admin)
        response = self.client.put(self.url, {"staff": ["accounting"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            has_permission_for_cooperative(
                cooperative_id=self.cooperative.id, role="staff", code="members.view"
            )
        )
        self.assertTrue(
            has_permission_for_cooperative(
                cooperative_id=self.cooperative.id, role="staff", code="accounting.edit"
            )
        )

    def test_restoring_default_modules_clears_overrides(self) -> None:
        from apps.roles_permissions.models import RoleModuleAccess

        self._auth(self.admin)
        default = sorted(self._default_staff_modules())
        response = self.client.put(self.url, {"staff": default}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            RoleModuleAccess.all_objects.filter(
                cooperative_id=self.cooperative.id, role="staff"
            ).exists()
        )
        self.assertFalse(
            has_permission_for_cooperative(
                cooperative_id=self.cooperative.id, role="staff", code="accounting.view"
            )
        )

    def test_invalid_module_rejected(self) -> None:
        self._auth(self.admin)
        response = self.client.put(self.url, {"staff": ["nonexistent"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_role_rejected(self) -> None:
        self._auth(self.admin)
        response = self.client.put(self.url, {"superadmin": ["members"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Isolation entre coopératives ----

    def test_overrides_do_not_leak_between_cooperatives(self) -> None:
        other_coop = Cooperative.objects.create(name="Coopérative Tanger", slug="tanger")
        other_admin = User.objects.create_user(
            username="tanger-admin",
            email="admin@tanger.ma",
            password="MotDePasseSolide123",
            cooperative=other_coop,
            role="admin",
        )

        self._auth(other_admin)
        response = self.client.put(self.url, {"staff": ["accounting"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # L'utilisateur staff de l'autre coopérative reste bloqué.
        self.assertFalse(
            has_permission_for_cooperative(
                cooperative_id=self.cooperative.id, role="staff", code="accounting.view"
            )
        )
        self.assertTrue(
            has_permission_for_cooperative(
                cooperative_id=other_coop.id, role="staff", code="accounting.view"
            )
        )
