"""
Tests du module billing.
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
from apps.partners.models import Partner
from apps.sales import services as sales_services
from apps.warehouses.models import Warehouse

User = get_user_model()


class BillingTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")

        self.admin = User.objects.create_user(
            username="admin", email="admin@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="admin",
        )
        self.accountant = User.objects.create_user(
            username="acct", email="acct@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="accountant",
        )
        self.staff = User.objects.create_user(
            username="staff", email="staff@argane.ma", password="MotDePasseSolide123",
            cooperative=self.cooperative, role="staff",
        )

        self.unit = Unit.objects.create(cooperative=self.cooperative, name="Kilogramme", symbol="kg", unit_type="weight")
        self.product = Product.objects.create(
            cooperative=self.cooperative, sku="PRD-00001", name={"fr": "Huile d'argane"}, unit=self.unit,
        )
        self.warehouse = Warehouse.objects.create(
            cooperative=self.cooperative, code="WH-0001", name="Entrepôt", is_default=True
        )
        self.customer = Partner.objects.create(
            cooperative=self.cooperative, code="PART-0001", name="Épicerie Al Baraka",
            is_customer=True, is_supplier=False, phone_number="0612345678", payment_terms_days=30,
        )

        self.invoices_url = reverse("billing:invoice-list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _manual_payload(self) -> dict:
        return {
            "customer_id": str(self.customer.id),
            "issue_date": "2026-07-01",
            "lines": [
                {"product_id": str(self.product.id), "quantity": "10", "unit_price": "50.00"},
            ],
        }

    # --- Création manuelle ---

    def test_accountant_can_create_manual_invoice(self) -> None:
        self._auth(self.accountant)
        response = self.client.post(self.invoices_url, self._manual_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["invoice_number"], "FAC-00001")
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("500.00"))

    def test_due_date_defaults_from_customer_payment_terms(self) -> None:
        self._auth(self.accountant)
        response = self.client.post(self.invoices_url, self._manual_payload(), format="json")
        self.assertEqual(response.data["due_date"], "2026-07-31")  # 2026-07-01 + 30 jours

    def test_staff_cannot_create_invoice(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.invoices_url, self._manual_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Génération depuis une commande de vente ---

    def test_generate_invoice_from_delivered_order(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("100"), actor=self.admin
        )
        order = sales_services.create_sales_order(
            cooperative=self.cooperative, customer=self.customer, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("20"), "unit_price": Decimal("50.00")}],
            actor=self.admin, order_date="2026-07-01",
        )
        sales_services.confirm_sales_order(order=order, actor=self.admin)
        line = order.lines.first()
        sales_services.record_sales_delivery(order=order, actor=self.admin, deliveries=[{"line_id": line.id, "quantity": Decimal("20")}])

        self._auth(self.accountant)
        response = self.client.post(
            reverse("billing:invoice-from-order"),
            {"order_id": str(order.id), "issue_date": "2026-07-05"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("1000.00"))
        self.assertEqual(response.data["order_number"], order.order_number)

    def test_cannot_generate_invoice_from_undelivered_order(self) -> None:
        order = sales_services.create_sales_order(
            cooperative=self.cooperative, customer=self.customer, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("20"), "unit_price": Decimal("50.00")}],
            actor=self.admin, order_date="2026-07-01",
        )
        self._auth(self.accountant)
        response = self.client.post(
            reverse("billing:invoice-from-order"),
            {"order_id": str(order.id), "issue_date": "2026-07-05"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_double_invoice_same_order(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("100"), actor=self.admin
        )
        order = sales_services.create_sales_order(
            cooperative=self.cooperative, customer=self.customer, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("20"), "unit_price": Decimal("50.00")}],
            actor=self.admin, order_date="2026-07-01",
        )
        sales_services.confirm_sales_order(order=order, actor=self.admin)
        line = order.lines.first()
        sales_services.record_sales_delivery(order=order, actor=self.admin, deliveries=[{"line_id": line.id, "quantity": Decimal("20")}])

        self._auth(self.accountant)
        payload = {"order_id": str(order.id), "issue_date": "2026-07-05"}
        self.client.post(reverse("billing:invoice-from-order"), payload, format="json")
        second = self.client.post(reverse("billing:invoice-from-order"), payload, format="json")
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Émission et paiements ---

    def test_issue_and_pay_invoice_fully(self) -> None:
        self._auth(self.accountant)
        invoice = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        self.client.post(reverse("billing:invoice-issue", args=[invoice["id"]]))

        pay_url = reverse("billing:invoice-payment", args=[invoice["id"]])
        response = self.client.post(pay_url, {"amount": "500.00", "payment_date": "2026-07-10", "payment_method": "cash"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "paid")
        self.assertEqual(Decimal(response.data["balance_due"]), Decimal("0.00"))

    def test_partial_payment_sets_status_partially_paid(self) -> None:
        self._auth(self.accountant)
        invoice = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        self.client.post(reverse("billing:invoice-issue", args=[invoice["id"]]))

        pay_url = reverse("billing:invoice-payment", args=[invoice["id"]])
        response = self.client.post(pay_url, {"amount": "200.00", "payment_date": "2026-07-10"})
        self.assertEqual(response.data["status"], "partially_paid")
        self.assertEqual(Decimal(response.data["balance_due"]), Decimal("300.00"))

    def test_payment_exceeding_balance_rejected(self) -> None:
        self._auth(self.accountant)
        invoice = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        self.client.post(reverse("billing:invoice-issue", args=[invoice["id"]]))

        pay_url = reverse("billing:invoice-payment", args=[invoice["id"]])
        response = self.client.post(pay_url, {"amount": "9999.00", "payment_date": "2026-07-10"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_pay_draft_invoice(self) -> None:
        self._auth(self.accountant)
        invoice = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        pay_url = reverse("billing:invoice-payment", args=[invoice["id"]])
        response = self.client.post(pay_url, {"amount": "100.00", "payment_date": "2026-07-10"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_second_payment_completes_invoice(self) -> None:
        self._auth(self.accountant)
        invoice = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        self.client.post(reverse("billing:invoice-issue", args=[invoice["id"]]))
        pay_url = reverse("billing:invoice-payment", args=[invoice["id"]])

        self.client.post(pay_url, {"amount": "200.00", "payment_date": "2026-07-10"})
        response = self.client.post(pay_url, {"amount": "300.00", "payment_date": "2026-07-15"})
        self.assertEqual(response.data["status"], "paid")

    # --- Annulation ---

    def test_cannot_cancel_invoice_with_payment(self) -> None:
        self._auth(self.accountant)
        invoice = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        self.client.post(reverse("billing:invoice-issue", args=[invoice["id"]]))
        self.client.post(reverse("billing:invoice-payment", args=[invoice["id"]]), {"amount": "100.00", "payment_date": "2026-07-10"})

        response = self.client.post(reverse("billing:invoice-cancel", args=[invoice["id"]]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_unpaid_draft_invoice(self) -> None:
        self._auth(self.accountant)
        invoice = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        response = self.client.post(reverse("billing:invoice-cancel", args=[invoice["id"]]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")

    def test_invoice_number_sequential(self) -> None:
        self._auth(self.accountant)
        first = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        second = self.client.post(self.invoices_url, self._manual_payload(), format="json").data
        self.assertEqual(first["invoice_number"], "FAC-00001")
        self.assertEqual(second["invoice_number"], "FAC-00002")
