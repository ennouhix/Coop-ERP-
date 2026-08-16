"""
Tests du module inventory.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Product, Unit
from apps.cooperatives.models import Cooperative
from apps.inventory import services
from apps.inventory.models import StockLevel
from apps.warehouses.models import Warehouse

User = get_user_model()


class InventoryTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")
        self.other_cooperative = Cooperative.objects.create(name="Autre Coop", slug="autre")

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="admin",
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="staff",
        )
        self.accountant = User.objects.create_user(
            username="acct",
            email="acct@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="accountant",
        )
        self.foreign_user = User.objects.create_user(
            username="foreign",
            email="foreign@autre.ma",
            password="MotDePasseSolide123",
            cooperative=self.other_cooperative,
            role="owner",
        )

        self.unit = Unit.objects.create(
            cooperative=self.cooperative, name="Kilogramme", symbol="kg", unit_type="weight"
        )
        self.product = Product.objects.create(
            cooperative=self.cooperative,
            sku="PRD-00001",
            name={"fr": "Huile d'argane"},
            unit=self.unit,
            minimum_stock_threshold=Decimal("10"),
        )
        self.warehouse_a = Warehouse.objects.create(
            cooperative=self.cooperative, code="WH-0001", name="Entrepôt A", is_default=True
        )
        self.warehouse_b = Warehouse.objects.create(
            cooperative=self.cooperative, code="WH-0002", name="Entrepôt B"
        )

        self.in_url = reverse("inventory:movement-in")
        self.out_url = reverse("inventory:movement-out")
        self.transfer_url = reverse("inventory:movement-transfer")
        self.levels_url = reverse("inventory:stock-level-list")
        self.movements_url = reverse("inventory:movement-list")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # --- Entrées ---

    def test_stock_in_creates_level_and_movement(self) -> None:
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "warehouse_id": str(self.warehouse_a.id),
            "quantity": "50",
        }
        response = self.client.post(self.in_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        level = StockLevel.objects.get(product=self.product, warehouse=self.warehouse_a)
        self.assertEqual(level.quantity, Decimal("50"))

    def test_multiple_stock_ins_accumulate(self) -> None:
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "warehouse_id": str(self.warehouse_a.id),
            "quantity": "30",
        }
        self.client.post(self.in_url, payload)
        self.client.post(self.in_url, payload)

        level = StockLevel.objects.get(product=self.product, warehouse=self.warehouse_a)
        self.assertEqual(level.quantity, Decimal("60"))

    # --- Sorties ---

    def test_stock_out_decreases_level(self) -> None:
        services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("50"),
            actor=self.admin,
        )
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "warehouse_id": str(self.warehouse_a.id),
            "quantity": "20",
        }
        response = self.client.post(self.out_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        level = StockLevel.objects.get(product=self.product, warehouse=self.warehouse_a)
        self.assertEqual(level.quantity, Decimal("30"))

    def test_stock_out_cannot_go_negative(self) -> None:
        services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("10"),
            actor=self.admin,
        )
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "warehouse_id": str(self.warehouse_a.id),
            "quantity": "50",
        }
        response = self.client.post(self.out_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        level = StockLevel.objects.get(product=self.product, warehouse=self.warehouse_a)
        self.assertEqual(level.quantity, Decimal("10"))  # inchangé

    def test_stock_out_on_never_stocked_product_fails_cleanly(self) -> None:
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "warehouse_id": str(self.warehouse_a.id),
            "quantity": "5",
        }
        response = self.client.post(self.out_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Transferts ---

    def test_transfer_moves_quantity_between_warehouses(self) -> None:
        services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("100"),
            actor=self.admin,
        )
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "from_warehouse_id": str(self.warehouse_a.id),
            "to_warehouse_id": str(self.warehouse_b.id),
            "quantity": "40",
        }
        response = self.client.post(self.transfer_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        level_a = StockLevel.objects.get(product=self.product, warehouse=self.warehouse_a)
        level_b = StockLevel.objects.get(product=self.product, warehouse=self.warehouse_b)
        self.assertEqual(level_a.quantity, Decimal("60"))
        self.assertEqual(level_b.quantity, Decimal("40"))

    def test_transfer_insufficient_stock_rejected(self) -> None:
        services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("10"),
            actor=self.admin,
        )
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "from_warehouse_id": str(self.warehouse_a.id),
            "to_warehouse_id": str(self.warehouse_b.id),
            "quantity": "50",
        }
        response = self.client.post(self.transfer_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transfer_same_warehouse_rejected(self) -> None:
        services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("10"),
            actor=self.admin,
        )
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "from_warehouse_id": str(self.warehouse_a.id),
            "to_warehouse_id": str(self.warehouse_a.id),
            "quantity": "5",
        }
        response = self.client.post(self.transfer_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Historique & isolation ---

    def test_movement_history_is_recorded(self) -> None:
        services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("50"),
            actor=self.admin,
        )
        services.record_stock_out(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("20"),
            actor=self.admin,
        )

        self._auth(self.admin)
        response = self.client.get(self.movements_url)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 2)

    def test_no_update_or_delete_endpoint_exists_for_movements(self) -> None:
        movement = services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("50"),
            actor=self.admin,
        )
        self._auth(self.admin)
        # Aucune route détaillée n'existe pour un mouvement : on ne peut
        # même pas former l'URL d'un PATCH/DELETE, l'immuabilité est
        # garantie par l'absence de la route elle-même.
        detail_url = f"{self.movements_url}{movement.id}/"
        response = self.client.patch(detail_url, {"quantity": "999"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accountant_can_view_but_not_edit_stock(self) -> None:
        self._auth(self.accountant)
        response = self.client.get(self.levels_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = {
            "product_id": str(self.product.id),
            "warehouse_id": str(self.warehouse_a.id),
            "quantity": "10",
        }
        response = self.client.post(self.in_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_reference_product_from_other_cooperative(self) -> None:
        self._auth(self.foreign_user)
        payload = {
            "product_id": str(self.product.id),
            "warehouse_id": str(self.warehouse_a.id),
            "quantity": "10",
        }
        response = self.client.post(self.in_url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_low_stock_endpoint_lists_products_under_threshold(self) -> None:
        services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("5"),
            actor=self.admin,
        )
        self._auth(self.admin)
        response = self.client.get(reverse("inventory:low-stock-list"))
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["is_below_threshold"])

    def test_low_stock_endpoint_excludes_products_above_threshold(self) -> None:
        services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse_a,
            quantity=Decimal("50"),
            actor=self.admin,
        )
        self._auth(self.admin)
        response = self.client.get(reverse("inventory:low-stock-list"))
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 0)

    def test_negative_quantity_rejected_by_serializer(self) -> None:
        self._auth(self.staff)
        payload = {
            "product_id": str(self.product.id),
            "warehouse_id": str(self.warehouse_a.id),
            "quantity": "-5",
        }
        response = self.client.post(self.in_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
