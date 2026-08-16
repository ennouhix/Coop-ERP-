"""
Tests du module catalog.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Category, Unit
from apps.catalog.services import create_product
from apps.cooperatives.models import Cooperative

User = get_user_model()


class CatalogTestCase(APITestCase):
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

        self.units_url = reverse("catalog:unit-list-create")
        self.categories_url = reverse("catalog:category-list-create")
        self.products_url = reverse("catalog:product-list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # --- Units ---

    def test_admin_can_create_unit(self) -> None:
        self._auth(self.admin)
        response = self.client.post(
            self.units_url, {"name": "Litre", "symbol": "L", "unit_type": "volume"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_staff_cannot_create_unit(self) -> None:
        self._auth(self.staff)
        response = self.client.post(
            self.units_url, {"name": "Litre", "symbol": "L", "unit_type": "volume"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_view_units(self) -> None:
        self._auth(self.staff)
        response = self.client.get(self.units_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Categories ---

    def test_create_category_with_translated_name(self) -> None:
        self._auth(self.admin)
        response = self.client.post(
            self.categories_url, {"name": {"fr": "Huiles", "ar": "الزيوت"}}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"]["fr"], "Huiles")
        self.assertEqual(response.data["name_display"], "Huiles")

    def test_category_cannot_be_its_own_parent(self) -> None:
        category = Category.objects.create(cooperative=self.cooperative, name={"fr": "Huiles"})
        self._auth(self.admin)
        url = reverse("catalog:category-detail", args=[category.id])
        response = self.client.patch(url, {"parent": str(category.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_category_hierarchy_cycle_is_rejected(self) -> None:
        parent = Category.objects.create(cooperative=self.cooperative, name={"fr": "Alimentaire"})
        child = Category.objects.create(
            cooperative=self.cooperative, name={"fr": "Huiles"}, parent=parent
        )

        self._auth(self.admin)
        url = reverse("catalog:category-detail", args=[parent.id])
        response = self.client.patch(url, {"parent": str(child.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Products ---

    def test_create_product_generates_sequential_sku(self) -> None:
        self._auth(self.admin)
        payload = {"name": {"fr": "Huile d'argane", "ar": "زيت الأركان"}, "unit": str(self.unit.id)}
        response = self.client.post(self.products_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sku"], "PRD-00001")

        second = self.client.post(
            self.products_url,
            {"name": {"fr": "Savon noir"}, "unit": str(self.unit.id)},
            format="json",
        )
        self.assertEqual(second.data["sku"], "PRD-00002")

    def test_product_name_display_resolves_by_language(self) -> None:
        product = create_product(
            cooperative=self.cooperative,
            name={"fr": "Huile d'argane", "ar": "زيت الأركان"},
            unit=self.unit,
        )
        self._auth(self.admin)
        url = reverse("catalog:product-detail", args=[product.id])

        response_fr = self.client.get(url, HTTP_ACCEPT_LANGUAGE="fr")
        self.assertEqual(response_fr.data["name_display"], "Huile d'argane")

        response_ar = self.client.get(url, HTTP_ACCEPT_LANGUAGE="ar")
        self.assertEqual(response_ar.data["name_display"], "زيت الأركان")

    def test_product_name_without_french_is_rejected(self) -> None:
        self._auth(self.admin)
        payload = {"name": {"ar": "زيت الأركان"}, "unit": str(self.unit.id)}
        response = self.client.post(self.products_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_barcode_in_same_cooperative_rejected(self) -> None:
        create_product(
            cooperative=self.cooperative,
            name={"fr": "Produit A"},
            unit=self.unit,
            barcode="1234567890",
        )
        self._auth(self.admin)
        payload = {"name": {"fr": "Produit B"}, "unit": str(self.unit.id), "barcode": "1234567890"}
        response = self.client.post(self.products_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_see_products_from_other_cooperative(self) -> None:
        create_product(cooperative=self.cooperative, name={"fr": "Produit A"}, unit=self.unit)
        self._auth(self.foreign_user)
        response = self.client.get(self.products_url)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 0)

    def test_deactivate_and_reactivate_product(self) -> None:
        product = create_product(
            cooperative=self.cooperative, name={"fr": "Produit A"}, unit=self.unit
        )
        self._auth(self.admin)

        deactivate_url = reverse("catalog:product-deactivate", args=[product.id])
        response = self.client.post(deactivate_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        reactivate_url = reverse("catalog:product-reactivate", args=[product.id])
        response = self.client.post(reactivate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_products_by_category(self) -> None:
        category = Category.objects.create(cooperative=self.cooperative, name={"fr": "Huiles"})
        product_in = create_product(
            cooperative=self.cooperative, name={"fr": "Huile"}, unit=self.unit, category=category
        )
        create_product(cooperative=self.cooperative, name={"fr": "Savon"}, unit=self.unit)

        self._auth(self.admin)
        response = self.client.get(self.products_url, {"category": str(category.id)})
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(product_in.id))

    def test_sku_immutable_on_update(self) -> None:
        product = create_product(
            cooperative=self.cooperative, name={"fr": "Produit A"}, unit=self.unit
        )
        self._auth(self.admin)
        url = reverse("catalog:product-detail", args=[product.id])
        response = self.client.patch(url, {"sku": "HACKED-9999"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.sku, "PRD-00001")
