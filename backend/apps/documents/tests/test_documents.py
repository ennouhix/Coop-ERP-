"""
Tests du module documents (M16) : génération et archivage des PDF
(bon de livraison, bon de commande fournisseur, bon de réception).

Vérifie le contenu réel des fichiers (PDF valides), l'archivage (une seule
copie par source, re-téléchargement identique) et l'isolation tenant.
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

from apps.catalog.models import Product, Unit
from apps.cooperatives.models import Cooperative
from apps.documents.models import DocumentArchive
from apps.partners.models import Partner
from apps.purchases import services as purchase_services
from apps.sales import services as sales_services
from apps.warehouses.models import Warehouse

User = get_user_model()


class DocumentsTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(
            name="Coopérative Argane",
            slug="argane",
            ice="001234567000012",
            legal_name="Argane SARL",
        )
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
            cooperative=self.cooperative, code="WH-0001", name="Entrepôt", is_default=True
        )
        self.customer = Partner.objects.create(
            cooperative=self.cooperative,
            code="PART-0001",
            name="Épicerie Al Baraka",
            is_customer=True,
            is_supplier=False,
        )
        self.supplier = Partner.objects.create(
            cooperative=self.cooperative,
            code="PART-0002",
            name="Coopérative Souss Fruits",
            is_customer=False,
            is_supplier=True,
            ice="002222222200022",
        )

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _create_sales_order(self):
        return sales_services.create_sales_order(
            cooperative=self.cooperative,
            customer=self.customer,
            warehouse=self.warehouse,
            lines=[
                {
                    "product": self.product,
                    "quantity_ordered": Decimal("5"),
                    "unit_price": Decimal("50.00"),
                }
            ],
            actor=self.admin,
            order_date=date(2026, 7, 1),
            notes="Livraison hebdomadaire.",
        )

    def _create_purchase_order(self):
        return purchase_services.create_purchase_order(
            cooperative=self.cooperative,
            supplier=self.supplier,
            warehouse=self.warehouse,
            lines=[
                {
                    "product": self.product,
                    "quantity_ordered": Decimal("20"),
                    "unit_price": Decimal("30.00"),
                }
            ],
            actor=self.admin,
            order_date=date(2026, 7, 2),
            expected_delivery_date=date(2026, 7, 10),
            notes="Merci de livrer avant la fin de semaine.",
        )

    @staticmethod
    def _pdf_content(response) -> bytes:  # noqa: ANN001
        return b"".join(response.streaming_content) if response.streaming else response.content

    # --- Bon de livraison (commande de vente) ---

    def test_delivery_note_pdf_is_valid(self) -> None:
        order = self._create_sales_order()
        self._auth(self.admin)
        url = reverse("documents:delivery-note-pdf", args=[order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("delivery_note", response["Content-Disposition"])
        content = self._pdf_content(response)
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertGreater(len(content), 500)

        archive = DocumentArchive.objects.get(
            cooperative=self.cooperative, doc_type="delivery_note", source_id=order.id
        )
        self.assertEqual(archive.source_number, order.order_number)
        self.assertTrue(archive.pdf_file.name.endswith(".pdf"))

    def test_delivery_note_archive_is_reused(self) -> None:
        order = self._create_sales_order()
        self._auth(self.admin)
        url = reverse("documents:delivery-note-pdf", args=[order.id])

        first = self._pdf_content(self.client.get(url))
        second = self._pdf_content(self.client.get(url))
        self.assertEqual(first, second)
        self.assertEqual(
            DocumentArchive.objects.filter(
                cooperative=self.cooperative, doc_type="delivery_note", source_id=order.id
            ).count(),
            1,
        )

    def test_staff_can_download_delivery_note(self) -> None:
        order = self._create_sales_order()
        self._auth(self.staff)
        url = reverse("documents:delivery-note-pdf", args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Bon de commande fournisseur ---

    def test_purchase_order_pdf_is_valid(self) -> None:
        order = self._create_purchase_order()
        self._auth(self.admin)
        url = reverse("documents:purchase-order-pdf", args=[order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = self._pdf_content(response)
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertIn("purchase_order", response["Content-Disposition"])

    # --- Bon de réception ---

    def test_receipt_pdf_is_valid(self) -> None:
        order = self._create_purchase_order()
        purchase_services.confirm_purchase_order(order=order, actor=self.admin)
        purchase_services.record_purchase_receipt(
            order=order,
            actor=self.admin,
            receipts=[{"line_id": order.lines.first().id, "quantity": Decimal("20")}],
        )
        self._auth(self.admin)
        url = reverse("documents:receipt-pdf", args=[order.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = self._pdf_content(response)
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertIn("receipt", response["Content-Disposition"])

    # --- Isolation entre coopératives ---

    def test_cannot_download_document_from_other_cooperative(self) -> None:
        other_coop = Cooperative.objects.create(name="Autre Coop", slug="autre")
        other_admin = User.objects.create_user(
            username="other",
            email="other@autre.ma",
            password="MotDePasseSolide123",
            cooperative=other_coop,
            role="admin",
        )
        order = self._create_purchase_order()
        self._auth(other_admin)
        url = reverse("documents:purchase-order-pdf", args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Personnalisation (DocumentTemplate) ---

    def test_template_apply_customization(self) -> None:
        from apps.documents.models import DocumentTemplate, DocumentTemplateType

        DocumentTemplate.objects.create(
            cooperative=self.cooperative,
            template_type=DocumentTemplateType.DELIVERY_NOTE,
            header_text="Coopérative BIO",
            footer_text="Paiement à réception",
            accent_color="#c1440e",
            show_logo=False,
        )
        order = self._create_sales_order()
        self._auth(self.admin)
        url = reverse("documents:delivery-note-pdf", args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self._pdf_content(response).startswith(b"%PDF"))

    # --- API de personnalisation des modèles ---

    def test_list_returns_three_types_with_defaults(self) -> None:
        self._auth(self.admin)
        response = self.client.get(reverse("documents:document-templates"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        types = {item["template_type"] for item in response.data}
        self.assertEqual(types, {"delivery_note", "purchase_order", "receipt"})
        for item in response.data:
            self.assertEqual(item["show_logo"], True)
            self.assertEqual(item["header_text"], "")

    def test_put_creates_and_updates_customization(self) -> None:
        self._auth(self.admin)
        url = reverse("documents:document-template-detail", args=["delivery_note"])
        payload = {
            "header_text": "Coopérative BIO",
            "footer_text": "Paiement à réception",
            "terms_text": "Livraison sous 48h.",
            "accent_color": "#c1440e",
            "show_logo": False,
        }
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["accent_color"], "#c1440e")

        updated = self.client.put(url, {**payload, "header_text": "Nouvel en-tête"}, format="json")
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["header_text"], "Nouvel en-tête")

        from apps.documents.models import DocumentTemplate

        self.assertEqual(
            DocumentTemplate.objects.filter(
                cooperative=self.cooperative, template_type="delivery_note"
            ).count(),
            1,
        )

    def test_staff_cannot_edit_templates(self) -> None:
        self._auth(self.staff)
        url = reverse("documents:document-template-detail", args=["receipt"])
        response = self.client.put(url, {"header_text": "Interdit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_invalid_template_type(self) -> None:
        self._auth(self.admin)
        url = reverse("documents:document-template-detail", args=["devis"])
        response = self.client.put(url, {"header_text": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_invalid_accent_color(self) -> None:
        self._auth(self.admin)
        url = reverse("documents:document-template-detail", args=["receipt"])
        response = self.client.put(
            url, {"accent_color": "pas-une-couleur", "show_logo": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
