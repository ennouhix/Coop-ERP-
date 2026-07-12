"""
Tests du module dashboard — construit un scénario réaliste traversant
membres, partenaires, stock, achats, ventes et facturation pour vérifier
que les agrégats retournés sont corrects.
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

from apps.billing import services as billing_services
from apps.catalog.models import Product, Unit
from apps.cooperatives.models import Cooperative
from apps.inventory import services as inventory_services
from apps.members.services import create_member
from apps.partners.models import Partner
from apps.purchases import services as purchases_services
from apps.sales import services as sales_services
from apps.warehouses.models import Warehouse

User = get_user_model()


class DashboardTestCase(APITestCase):
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

        self.unit = Unit.objects.create(cooperative=self.cooperative, name="Kilogramme", symbol="kg", unit_type="weight")
        self.product = Product.objects.create(
            cooperative=self.cooperative, sku="PRD-00001", name={"fr": "Huile d'argane"}, unit=self.unit,
            reference_purchase_price=Decimal("20.00"),
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

        create_member(cooperative=self.cooperative, first_name="Ahmed", last_name="Ouazzani", phone_number="0699999999")

        self.summary_url = reverse("dashboard:summary")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_staff_cannot_access_dashboard(self) -> None:
        self._auth(self.staff)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_dashboard(self) -> None:
        self._auth(self.admin)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_members_count_reflects_active_members(self) -> None:
        self._auth(self.admin)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.data["members"]["active_count"], 1)

    def test_partners_counts_correct(self) -> None:
        self._auth(self.admin)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.data["partners"]["active_customers"], 1)
        self.assertEqual(response.data["partners"]["active_suppliers"], 1)

    def test_stock_value_and_low_stock_count(self) -> None:
        self.product.minimum_stock_threshold = Decimal("50")
        self.product.save(update_fields=["minimum_stock_threshold"])
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("10"), actor=self.admin
        )

        self._auth(self.admin)
        response = self.client.get(self.summary_url)
        # 10 kg x 20.00 (prix d'achat de référence) = 200.00
        self.assertEqual(Decimal(response.data["stock"]["total_stock_value"]), Decimal("200.00"))
        self.assertEqual(response.data["stock"]["low_stock_lines_count"], 1)

    def test_sales_revenue_reflects_issued_invoices_in_period(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("100"), actor=self.admin
        )
        order = sales_services.create_sales_order(
            cooperative=self.cooperative, customer=self.customer, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("10"), "unit_price": Decimal("50.00")}],
            actor=self.admin, order_date=date(2026, 7, 5),
        )
        sales_services.confirm_sales_order(order=order, actor=self.admin)
        line = order.lines.first()
        sales_services.record_sales_delivery(order=order, actor=self.admin, deliveries=[{"line_id": line.id, "quantity": Decimal("10")}])
        invoice = billing_services.generate_invoice_from_sales_order(order=order, actor=self.admin, issue_date=date(2026, 7, 6))
        billing_services.issue_invoice(invoice=invoice, actor=self.admin)

        self._auth(self.admin)
        response = self.client.get(self.summary_url, {"date_from": "2026-07-01", "date_to": "2026-07-31"})
        self.assertEqual(Decimal(response.data["sales"]["revenue_invoiced_period"]), Decimal("500.00"))
        self.assertEqual(response.data["sales"]["orders_delivered"], 1)

    def test_revenue_excludes_invoices_outside_period(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("100"), actor=self.admin
        )
        order = sales_services.create_sales_order(
            cooperative=self.cooperative, customer=self.customer, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("10"), "unit_price": Decimal("50.00")}],
            actor=self.admin, order_date=date(2026, 1, 5),
        )
        sales_services.confirm_sales_order(order=order, actor=self.admin)
        line = order.lines.first()
        sales_services.record_sales_delivery(order=order, actor=self.admin, deliveries=[{"line_id": line.id, "quantity": Decimal("10")}])
        invoice = billing_services.generate_invoice_from_sales_order(order=order, actor=self.admin, issue_date=date(2026, 1, 6))
        billing_services.issue_invoice(invoice=invoice, actor=self.admin)

        self._auth(self.admin)
        response = self.client.get(self.summary_url, {"date_from": "2026-07-01", "date_to": "2026-07-31"})
        self.assertEqual(Decimal(response.data["sales"]["revenue_invoiced_period"]), Decimal("0"))

    def test_purchases_spend_reflects_confirmed_orders(self) -> None:
        purchases_services.create_purchase_order(
            cooperative=self.cooperative, supplier=self.supplier, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("20"), "unit_price": Decimal("15.00")}],
            actor=self.admin, order_date=date(2026, 7, 2),
        )
        order = purchases_services.create_purchase_order(
            cooperative=self.cooperative, supplier=self.supplier, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("20"), "unit_price": Decimal("15.00")}],
            actor=self.admin, order_date=date(2026, 7, 2),
        )
        purchases_services.confirm_purchase_order(order=order, actor=self.admin)

        self._auth(self.admin)
        response = self.client.get(self.summary_url, {"date_from": "2026-07-01", "date_to": "2026-07-31"})
        # Un seul des deux ordres est CONFIRMED (l'autre reste DRAFT, exclu du calcul)
        self.assertEqual(Decimal(response.data["purchases"]["spend_confirmed_period"]), Decimal("300.00"))
        self.assertEqual(response.data["purchases"]["orders_draft"], 1)
        self.assertEqual(response.data["purchases"]["orders_confirmed"], 1)

    def test_billing_outstanding_and_overdue(self) -> None:
        inventory_services.record_stock_in(
            product=self.product, warehouse=self.warehouse, quantity=Decimal("100"), actor=self.admin
        )
        order = sales_services.create_sales_order(
            cooperative=self.cooperative, customer=self.customer, warehouse=self.warehouse,
            lines=[{"product": self.product, "quantity_ordered": Decimal("10"), "unit_price": Decimal("50.00")}],
            actor=self.admin, order_date=date(2026, 1, 5),
        )
        sales_services.confirm_sales_order(order=order, actor=self.admin)
        line = order.lines.first()
        sales_services.record_sales_delivery(order=order, actor=self.admin, deliveries=[{"line_id": line.id, "quantity": Decimal("10")}])
        invoice = billing_services.generate_invoice_from_sales_order(
            order=order, actor=self.admin, issue_date=date(2026, 1, 6), due_date=date(2026, 1, 20)
        )
        billing_services.issue_invoice(invoice=invoice, actor=self.admin)

        self._auth(self.admin)
        response = self.client.get(self.summary_url)
        self.assertEqual(Decimal(response.data["billing"]["total_outstanding_balance"]), Decimal("500.00"))
        self.assertEqual(response.data["billing"]["overdue_invoices_count"], 1)  # échéance largement dépassée

    def test_user_sees_only_own_cooperative_data(self) -> None:
        other_cooperative = Cooperative.objects.create(name="Autre Coop", slug="autre")
        other_admin = User.objects.create_user(
            username="other_admin", email="other@autre.ma", password="MotDePasseSolide123",
            cooperative=other_cooperative, role="admin",
        )
        create_member(cooperative=self.cooperative, first_name="X", last_name="Y", phone_number="0600000000")

        self._auth(other_admin)
        response = self.client.get(self.summary_url)
        self.assertEqual(response.data["members"]["active_count"], 0)
