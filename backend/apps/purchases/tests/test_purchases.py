"""
Tests du module purchases — couvre le cycle complet DRAFT -> CONFIRMED ->
(PARTIALLY_)RECEIVED, et vérifie que la réception déclenche bien de vrais
mouvements de stock (intégration avec l'Epic 8).
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
from apps.inventory.models import StockLevel, StockMovement
from apps.partners.models import Partner
from apps.purchases.models import PurchaseOrder
from apps.warehouses.models import Warehouse

User = get_user_model()


class PurchaseOrderTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")

        self.admin = User.objects.create_user(
            username="admin", email="admin@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="admin",
        )
        self.staff = User.objects.create_user(
            username="staff", email="staff@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="staff",
        )
        self.accountant = User.objects.create_user(
            username="acct", email="acct@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="accountant",
        )

        self.unit = Unit.objects.create(cooperative=self.cooperative, name="Kilogramme", symbol="kg", unit_type="weight")
        self.product = Product.objects.create(
            cooperative=self.cooperative, sku="PRD-00001", name={"fr": "Amandes brutes"}, unit=self.unit,
        )
        self.warehouse = Warehouse.objects.create(
            cooperative=self.cooperative, code="WH-0001", name="Entrepôt Principal", is_default=True
        )
        self.supplier = Partner.objects.create(
            cooperative=self.cooperative, code="PART-0001", name="Fournisseur Amandes",
            is_customer=False, is_supplier=True, phone_number="0612345678",
        )
        self.non_supplier = Partner.objects.create(
            cooperative=self.cooperative, code="PART-0002", name="Client Seulement",
            is_customer=True, is_supplier=False, phone_number="0611111111",
        )

        self.list_url = reverse("purchases:order-list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _valid_payload(self) -> dict:
        return {
            "supplier_id": str(self.supplier.id),
            "warehouse_id": str(self.warehouse.id),
            "order_date": "2026-07-01",
            "lines": [
                {"product_id": str(self.product.id), "quantity_ordered": "100", "unit_price": "12.50"},
            ],
        }

    # --- Création ---

    def test_admin_can_create_draft_order(self) -> None:
        self._auth(self.admin)
        response = self.client.post(self.list_url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["order_number"], "PO-00001")
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("1250.00"))

    def test_staff_cannot_create_order(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.list_url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_order_from_non_supplier(self) -> None:
        self._auth(self.admin)
        payload = {**self._valid_payload(), "supplier_id": str(self.non_supplier.id)}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_create_order_without_lines(self) -> None:
        self._auth(self.admin)
        payload = {**self._valid_payload(), "lines": []}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Confirmation ---

    def test_confirm_draft_order(self) -> None:
        self._auth(self.admin)
        order = self.client.post(self.list_url, self._valid_payload(), format="json").data
        url = reverse("purchases:order-confirm", args=[order["id"]])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "confirmed")

    def test_cannot_confirm_already_confirmed_order(self) -> None:
        self._auth(self.admin)
        order = self.client.post(self.list_url, self._valid_payload(), format="json").data
        confirm_url = reverse("purchases:order-confirm", args=[order["id"]])
        self.client.post(confirm_url)
        response = self.client.post(confirm_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Réception : le cœur de l'intégration avec le Stock ---

    def test_full_receipt_creates_stock_movement_and_updates_level(self) -> None:
        self._auth(self.admin)
        order_data = self.client.post(self.list_url, self._valid_payload(), format="json").data
        self.client.post(reverse("purchases:order-confirm", args=[order_data["id"]]))

        line_id = order_data["lines"][0]["id"]
        self._auth(self.staff)  # la réception est une tâche de terrain (STAFF autorisé)
        receive_url = reverse("purchases:order-receive", args=[order_data["id"]])
        response = self.client.post(receive_url, {"receipts": [{"line_id": line_id, "quantity": "100"}]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "received")

        level = StockLevel.objects.get(product=self.product, warehouse=self.warehouse)
        self.assertEqual(level.quantity, Decimal("100"))

        movement = StockMovement.objects.get(reference=order_data["order_number"])
        self.assertEqual(movement.reason, "purchase")
        self.assertEqual(movement.quantity, Decimal("100"))

    def test_partial_receipt_sets_status_partially_received(self) -> None:
        self._auth(self.admin)
        order_data = self.client.post(self.list_url, self._valid_payload(), format="json").data
        self.client.post(reverse("purchases:order-confirm", args=[order_data["id"]]))

        line_id = order_data["lines"][0]["id"]
        receive_url = reverse("purchases:order-receive", args=[order_data["id"]])
        response = self.client.post(receive_url, {"receipts": [{"line_id": line_id, "quantity": "60"}]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "partially_received")

        level = StockLevel.objects.get(product=self.product, warehouse=self.warehouse)
        self.assertEqual(level.quantity, Decimal("60"))

    def test_second_partial_receipt_completes_order(self) -> None:
        self._auth(self.admin)
        order_data = self.client.post(self.list_url, self._valid_payload(), format="json").data
        self.client.post(reverse("purchases:order-confirm", args=[order_data["id"]]))
        line_id = order_data["lines"][0]["id"]
        receive_url = reverse("purchases:order-receive", args=[order_data["id"]])

        self.client.post(receive_url, {"receipts": [{"line_id": line_id, "quantity": "60"}]}, format="json")
        response = self.client.post(receive_url, {"receipts": [{"line_id": line_id, "quantity": "40"}]}, format="json")

        self.assertEqual(response.data["status"], "received")
        level = StockLevel.objects.get(product=self.product, warehouse=self.warehouse)
        self.assertEqual(level.quantity, Decimal("100"))

    def test_cannot_receive_more_than_ordered(self) -> None:
        self._auth(self.admin)
        order_data = self.client.post(self.list_url, self._valid_payload(), format="json").data
        self.client.post(reverse("purchases:order-confirm", args=[order_data["id"]]))
        line_id = order_data["lines"][0]["id"]

        receive_url = reverse("purchases:order-receive", args=[order_data["id"]])
        response = self.client.post(receive_url, {"receipts": [{"line_id": line_id, "quantity": "150"}]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        level_exists = StockLevel.objects.filter(product=self.product, warehouse=self.warehouse).exists()
        self.assertFalse(level_exists)  # rien n'a dû être créé

    def test_cannot_receive_draft_order(self) -> None:
        self._auth(self.admin)
        order_data = self.client.post(self.list_url, self._valid_payload(), format="json").data
        line_id = order_data["lines"][0]["id"]

        receive_url = reverse("purchases:order-receive", args=[order_data["id"]])
        response = self.client.post(receive_url, {"receipts": [{"line_id": line_id, "quantity": "10"}]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accountant_cannot_receive_order(self) -> None:
        self._auth(self.admin)
        order_data = self.client.post(self.list_url, self._valid_payload(), format="json").data
        self.client.post(reverse("purchases:order-confirm", args=[order_data["id"]]))
        line_id = order_data["lines"][0]["id"]

        self._auth(self.accountant)
        receive_url = reverse("purchases:order-receive", args=[order_data["id"]])
        response = self.client.post(receive_url, {"receipts": [{"line_id": line_id, "quantity": "10"}]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Annulation ---

    def test_cancel_draft_order(self) -> None:
        self._auth(self.admin)
        order_data = self.client.post(self.list_url, self._valid_payload(), format="json").data
        url = reverse("purchases:order-cancel", args=[order_data["id"]])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")

    def test_cannot_cancel_order_with_receipts(self) -> None:
        self._auth(self.admin)
        order_data = self.client.post(self.list_url, self._valid_payload(), format="json").data
        self.client.post(reverse("purchases:order-confirm", args=[order_data["id"]]))
        line_id = order_data["lines"][0]["id"]
        receive_url = reverse("purchases:order-receive", args=[order_data["id"]])
        self.client.post(receive_url, {"receipts": [{"line_id": line_id, "quantity": "10"}]}, format="json")

        cancel_url = reverse("purchases:order-cancel", args=[order_data["id"]])
        response = self.client.post(cancel_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_number_immutable_and_sequential(self) -> None:
        self._auth(self.admin)
        first = self.client.post(self.list_url, self._valid_payload(), format="json").data
        second = self.client.post(self.list_url, self._valid_payload(), format="json").data
        self.assertEqual(first["order_number"], "PO-00001")
        self.assertEqual(second["order_number"], "PO-00002")
