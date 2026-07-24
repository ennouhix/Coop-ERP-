"""
Tests du module audit.

Vérifie que les points d'instrumentation ajoutés rétroactivement dans les
autres modules (authentication, users, inventory, purchases, sales,
billing) créent bien une entrée AuditLog — pas seulement que le journal
fonctionne isolément.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.models import AuditLog
from apps.billing import services as billing_services
from apps.catalog.models import Product, Unit
from apps.cooperatives.models import Cooperative
from apps.inventory import services as inventory_services
from apps.partners.models import Partner
from apps.purchases import services as purchases_services
from apps.sales import services as sales_services
from apps.users import services as users_services
from apps.warehouses.models import Warehouse

User = get_user_model()


class AuditLogTestCase(APITestCase):
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

        self.unit = Unit.objects.create(cooperative=self.cooperative, name="Kilogramme", symbol="kg", unit_type="weight")
        self.product = Product.objects.create(
            cooperative=self.cooperative, sku="PRD-00001", name={"fr": "Huile d'argane"}, unit=self.unit,
        )
        self.warehouse = Warehouse.objects.create(
            cooperative=self.cooperative, code="WH-0001", name="Entrepôt", is_default=True
        )
        self.customer = Partner.objects.create(
            cooperative=self.cooperative, code="PART-0001", name="Client A",
            is_customer=True, is_supplier=False, phone_number="0612345678",
        )
        self.supplier = Partner.objects.create(
            cooperative=self.cooperative, code="PART-0002", name="Fournisseur A",
            is_customer=False, is_supplier=True, phone_number="0611111111",
        )

        self.logs_url = reverse("audit:log-list")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # --- Authentification ---

    def test_login_creates_audit_entry(self) -> None:
        self.client.post(reverse("authentication:login"), {"email": "owner@argane.ma", "password": "MotDePasseSolide123"})
        self.assertTrue(AuditLog.objects.filter(cooperative=self.cooperative, action="user.login").exists())

    def test_login_audit_entry_captures_ip(self) -> None:
        self.client.post(
            reverse("authentication:login"), {"email": "owner@argane.ma", "password": "MotDePasseSolide123"}
        )
        log = AuditLog.objects.get(action="user.login")
        self.assertIsNotNone(log.ip_address)

    def test_failed_login_does_not_create_audit_entry(self) -> None:
        self.client.post(reverse("authentication:login"), {"email": "owner@argane.ma", "password": "MauvaisMotDePasse"})
        self.assertFalse(AuditLog.objects.filter(action="user.login").exists())

    # --- Gestion d'équipe ---

    def test_role_change_creates_audit_entry_with_metadata(self) -> None:
        users_services.change_user_role(actor=self.owner, target_user=self.staff, new_role="admin")
        log = AuditLog.objects.get(action="user.role_changed")
        self.assertEqual(log.metadata["old_role"], "staff")
        self.assertEqual(log.metadata["new_role"], "admin")

    def test_deactivation_creates_audit_entry(self) -> None:
        users_services.deactivate_user(actor=self.owner, target_user=self.staff)
        self.assertTrue(AuditLog.objects.filter(action="user.deactivated", target_id=str(self.staff.id)).exists())

    # --- Stock ---

    def test_stock_in_creates_audit_entry(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("50"), actor=self.admin
        )
        self.assertTrue(AuditLog.objects.filter(action="stock.in").exists())

    def test_stock_transfer_creates_audit_entry(self) -> None:
        second_warehouse = Warehouse.objects.create(cooperative=self.cooperative, code="WH-0002", name="Entrepôt 2")
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("50"), actor=self.admin
        )
        inventory_services.record_stock_transfer(
            product=self.product, from_warehouse=self.warehouse, to_warehouse=second_warehouse,
            quantity=Decimal("10"), actor=self.admin,
        )
        self.assertTrue(AuditLog.objects.filter(action="stock.transfer").exists())

    # --- Achats / Ventes / Facturation ---

    def test_purchase_order_lifecycle_creates_audit_entries(self) -> None:
        order = purchases_services.create_purchase_order(
            cooperative=self.cooperative, supplier=self.supplier, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("20"), "unit_price": Decimal("15.00")}],
            actor=self.admin, order_date=date(2026, 7, 1),
        )
        purchases_services.confirm_purchase_order(order=order, actor=self.admin)
        line = order.lines.first()
        purchases_services.record_purchase_receipt(
            order=order, actor=self.admin, receipts=[{"line_id": line.id, "quantity": Decimal("20")}]
        )

        self.assertTrue(AuditLog.objects.filter(action="purchase_order.confirmed").exists())
        self.assertTrue(AuditLog.objects.filter(action="purchase_order.received").exists())

    def test_invoice_payment_creates_audit_entry(self) -> None:
        invoice = billing_services.create_manual_invoice(
            cooperative=self.cooperative, customer=self.customer,
            lines=[{"product": self.product, "description": "", "quantity": Decimal("10"), "unit_price": Decimal("50.00")}],
            actor=self.admin, issue_date=date(2026, 7, 1),
        )
        billing_services.issue_invoice(invoice=invoice, actor=self.admin)
        billing_services.record_payment(invoice=invoice, amount=Decimal("200"), payment_date=date(2026, 7, 5), actor=self.admin)

        log = AuditLog.objects.get(action="invoice.payment_recorded")
        self.assertEqual(log.metadata["amount"], "200")

    # --- Endpoint de consultation ---

    def test_admin_can_list_audit_logs(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("50"), actor=self.admin
        )
        self._auth(self.admin)
        response = self.client.get(self.logs_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertGreaterEqual(len(results), 1)

    def test_staff_cannot_access_audit_log(self) -> None:
        self._auth(self.staff)
        response = self.client.get(self.logs_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_audit_log_by_action_prefix(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("50"), actor=self.admin
        )
        users_services.change_user_role(actor=self.owner, target_user=self.staff, new_role="admin")

        self._auth(self.admin)
        response = self.client.get(self.logs_url, {"action": "stock."})
        results = response.data["results"] if "results" in response.data else response.data
        self.assertTrue(all(r["action"].startswith("stock.") for r in results))

    def test_audit_log_is_tenant_isolated(self) -> None:
        other_cooperative = Cooperative.objects.create(name="Autre Coop", slug="autre")
        other_admin = User.objects.create_user(
            username="other_admin", email="other@autre.ma", password="MotDePasseSolide123",
            cooperative=other_cooperative, role="admin",
        )
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("50"), actor=self.admin
        )

        self._auth(other_admin)
        response = self.client.get(self.logs_url)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 0)

    def test_no_write_endpoint_exists_for_audit_log(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("50"), actor=self.admin
        )
        log = AuditLog.objects.first()
        self._auth(self.admin)
        response = self.client.patch(f"{self.logs_url}{log.id}/", {"action": "hacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
