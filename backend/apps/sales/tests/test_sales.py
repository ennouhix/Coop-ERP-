"""
Tests du module sales.
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
from apps.inventory import services as inventory_services
from apps.inventory.models import StockLevel, StockMovement
from apps.partners.models import Partner
from apps.warehouses.models import Warehouse

User = get_user_model()


class SalesOrderTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")

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

        self.unit = Unit.objects.create(
            cooperative=self.cooperative, name="Kilogramme", symbol="kg", unit_type="weight"
        )
        self.product = Product.objects.create(
            cooperative=self.cooperative,
            sku="PRD-00001",
            name={"fr": "Huile d'argane"},
            unit=self.unit,
        )
        self.warehouse = Warehouse.objects.create(
            cooperative=self.cooperative, code="WH-0001", name="Entrepôt Principal", is_default=True
        )
        self.customer = Partner.objects.create(
            cooperative=self.cooperative,
            code="PART-0001",
            name="Épicerie Al Baraka",
            is_customer=True,
            is_supplier=False,
            phone_number="0612345678",
        )
        self.non_customer = Partner.objects.create(
            cooperative=self.cooperative,
            code="PART-0002",
            name="Fournisseur Seulement",
            is_customer=False,
            is_supplier=True,
            phone_number="0611111111",
        )

        # Stock initial disponible pour les scénarios de livraison.
        inventory_services.record_stock_in(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal("100"),
            actor=self.staff,
        )

        self.list_url = reverse("sales:order-list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _valid_payload(self, quantity: str = "30") -> dict:
        return {
            "customer_id": str(self.customer.id),
            "warehouse_id": str(self.warehouse.id),
            "order_date": "2026-07-01",
            "lines": [
                {
                    "product_id": str(self.product.id),
                    "quantity_ordered": quantity,
                    "unit_price": "45.00",
                },
            ],
        }

    # --- Création ---

    def test_staff_can_create_draft_order(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.list_url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["order_number"], "SO-00001")

    def test_cannot_sell_to_non_customer(self) -> None:
        self._auth(self.staff)
        payload = {**self._valid_payload(), "customer_id": str(self.non_customer.id)}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accountant_cannot_create_order(self) -> None:
        self._auth(self.accountant)
        response = self.client.post(self.list_url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Livraison : intégration avec le Stock ---

    def test_full_delivery_creates_stock_out_movement(self) -> None:
        self._auth(self.staff)
        order = self.client.post(self.list_url, self._valid_payload("30"), format="json").data
        self.client.post(reverse("sales:order-confirm", args=[order["id"]]))

        line_id = order["lines"][0]["id"]
        deliver_url = reverse("sales:order-deliver", args=[order["id"]])
        response = self.client.post(
            deliver_url, {"deliveries": [{"line_id": line_id, "quantity": "30"}]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "delivered")

        level = StockLevel.objects.get(product=self.product, warehouse=self.warehouse)
        self.assertEqual(level.quantity, Decimal("70"))  # 100 initial - 30 livrés

        movement = StockMovement.objects.get(reference=order["order_number"])
        self.assertEqual(movement.movement_type, "out")
        self.assertEqual(movement.reason, "sale")

    def test_delivery_exceeding_stock_is_rejected(self) -> None:
        self._auth(self.staff)
        order = self.client.post(self.list_url, self._valid_payload("30"), format="json").data
        self.client.post(reverse("sales:order-confirm", args=[order["id"]]))

        # On vide le stock ailleurs pour simuler une rupture avant livraison.
        inventory_services.record_stock_out(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("90"), actor=self.staff
        )

        line_id = order["lines"][0]["id"]
        deliver_url = reverse("sales:order-deliver", args=[order["id"]])
        response = self.client.post(
            deliver_url, {"deliveries": [{"line_id": line_id, "quantity": "30"}]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # La commande ne doit pas être passée à "delivered" si la livraison a échoué.
        order_check = self.client.get(reverse("sales:order-detail", args=[order["id"]]))
        self.assertEqual(order_check.data["status"], "confirmed")

    def test_partial_delivery_sets_status_partially_delivered(self) -> None:
        self._auth(self.staff)
        order = self.client.post(self.list_url, self._valid_payload("30"), format="json").data
        self.client.post(reverse("sales:order-confirm", args=[order["id"]]))

        line_id = order["lines"][0]["id"]
        deliver_url = reverse("sales:order-deliver", args=[order["id"]])
        response = self.client.post(
            deliver_url, {"deliveries": [{"line_id": line_id, "quantity": "10"}]}, format="json"
        )
        self.assertEqual(response.data["status"], "partially_delivered")

    # --- Contrôle d'encours ---

    def test_confirm_blocked_when_exceeding_credit_limit(self) -> None:
        self.customer.credit_limit = Decimal("500")
        self.customer.save(update_fields=["credit_limit"])

        self._auth(self.staff)
        # 30 x 45.00 = 1350, largement au-dessus de la limite de 500.
        order = self.client.post(self.list_url, self._valid_payload("30"), format="json").data
        response = self.client.post(reverse("sales:order-confirm", args=[order["id"]]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_allowed_within_credit_limit(self) -> None:
        self.customer.credit_limit = Decimal("5000")
        self.customer.save(update_fields=["credit_limit"])

        self._auth(self.staff)
        order = self.client.post(self.list_url, self._valid_payload("30"), format="json").data
        response = self.client.post(reverse("sales:order-confirm", args=[order["id"]]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_credit_limit_means_unlimited(self) -> None:
        # credit_limit par défaut = 0, interprété comme "pas de limite".
        self._auth(self.staff)
        order = self.client.post(self.list_url, self._valid_payload("30"), format="json").data
        response = self.client.post(reverse("sales:order-confirm", args=[order["id"]]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Annulation ---

    def test_cannot_cancel_order_with_deliveries(self) -> None:
        self._auth(self.staff)
        order = self.client.post(self.list_url, self._valid_payload("30"), format="json").data
        self.client.post(reverse("sales:order-confirm", args=[order["id"]]))
        line_id = order["lines"][0]["id"]
        self.client.post(
            reverse("sales:order-deliver", args=[order["id"]]),
            {"deliveries": [{"line_id": line_id, "quantity": "10"}]},
            format="json",
        )

        response = self.client.post(reverse("sales:order-cancel", args=[order["id"]]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_number_sequential(self) -> None:
        self._auth(self.staff)
        first = self.client.post(self.list_url, self._valid_payload("10"), format="json").data
        second = self.client.post(self.list_url, self._valid_payload("10"), format="json").data
        self.assertEqual(first["order_number"], "SO-00001")
        self.assertEqual(second["order_number"], "SO-00002")
