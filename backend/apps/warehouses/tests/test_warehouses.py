"""
Tests du module warehouses.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.cooperatives.models import Cooperative
from apps.warehouses.models import Warehouse
from apps.warehouses.services import create_warehouse

User = get_user_model()


class WarehouseTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")
        self.other_cooperative = Cooperative.objects.create(name="Autre Coop", slug="autre")

        self.admin = User.objects.create_user(
            username="admin", email="admin@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="admin",
        )
        self.staff = User.objects.create_user(
            username="staff", email="staff@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="staff",
        )
        self.foreign_user = User.objects.create_user(
            username="foreign", email="foreign@autre.ma", password="MotDePasseSolide123",
            cooperative=self.other_cooperative, role="owner",
        )

        self.list_url = reverse("warehouses:list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_first_warehouse_becomes_default_automatically(self) -> None:
        self._auth(self.admin)
        response = self.client.post(self.list_url, {"name": "Entrepôt Principal"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_default"])

    def test_second_warehouse_is_not_default_by_default(self) -> None:
        self._auth(self.admin)
        self.client.post(self.list_url, {"name": "Entrepôt Principal"})
        response = self.client.post(self.list_url, {"name": "Entrepôt Secondaire"})
        self.assertFalse(response.data["is_default"])

    def test_warehouse_codes_are_sequential(self) -> None:
        self._auth(self.admin)
        self.client.post(self.list_url, {"name": "Entrepôt A"})
        response = self.client.post(self.list_url, {"name": "Entrepôt B"})
        self.assertEqual(response.data["code"], "WH-0002")

    def test_setting_new_default_unsets_previous_one(self) -> None:
        self._auth(self.admin)
        first = self.client.post(self.list_url, {"name": "Entrepôt A"}).data
        second = self.client.post(self.list_url, {"name": "Entrepôt B"}).data

        url = reverse("warehouses:set-default", args=[second["id"]])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_default"])

        first_warehouse = Warehouse.objects.get(pk=first["id"])
        self.assertFalse(first_warehouse.is_default)

    def test_cannot_deactivate_default_warehouse(self) -> None:
        self._auth(self.admin)
        warehouse = self.client.post(self.list_url, {"name": "Entrepôt Unique"}).data
        url = reverse("warehouses:deactivate", args=[warehouse["id"]])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_deactivate_non_default_warehouse(self) -> None:
        self._auth(self.admin)
        self.client.post(self.list_url, {"name": "Entrepôt A"})
        second = self.client.post(self.list_url, {"name": "Entrepôt B"}).data

        url = reverse("warehouses:deactivate", args=[second["id"]])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_staff_cannot_create_warehouse(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.list_url, {"name": "Entrepôt Non Autorisé"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_view_warehouses(self) -> None:
        create_warehouse(cooperative=self.cooperative, name="Entrepôt A")
        self._auth(self.staff)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_must_belong_to_same_cooperative(self) -> None:
        self._auth(self.admin)
        response = self.client.post(
            self.list_url, {"name": "Entrepôt A", "manager": str(self.foreign_user.id)}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_see_warehouses_from_other_cooperative(self) -> None:
        create_warehouse(cooperative=self.cooperative, name="Entrepôt A")
        self._auth(self.foreign_user)
        response = self.client.get(self.list_url)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 0)

    def test_reactivate_warehouse(self) -> None:
        create_warehouse(cooperative=self.cooperative, name="Entrepôt A")
        second = create_warehouse(cooperative=self.cooperative, name="Entrepôt B")
        self._auth(self.admin)

        deactivate_url = reverse("warehouses:deactivate", args=[second.id])
        self.client.post(deactivate_url)

        reactivate_url = reverse("warehouses:reactivate", args=[second.id])
        response = self.client.post(reactivate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        second.refresh_from_db()
        self.assertTrue(second.is_active)

    def test_code_immutable_on_update(self) -> None:
        warehouse = create_warehouse(cooperative=self.cooperative, name="Entrepôt A")
        self._auth(self.admin)
        url = reverse("warehouses:detail", args=[warehouse.id])
        response = self.client.patch(url, {"code": "HACKED-9999"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        warehouse.refresh_from_db()
        self.assertEqual(warehouse.code, "WH-0001")
