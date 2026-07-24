"""
Commande de seed : crée une coopérative de démonstration avec un jeu de
données complet et cohérent — pas juste des lignes vides, mais un vrai
cycle métier déjà exécuté (achat reçu, vente livrée, facture partiellement
payée) pour que le dashboard et les écrans affichent immédiatement
quelque chose de significatif.

Usage :
    python manage.py seed_demo_data
    python manage.py seed_demo_data --reset   # supprime la démo existante avant de la recréer

Réutilise exclusivement les services métier déjà construits (jamais de
création directe de modèle qui contournerait les règles métier) — cette
commande est un utilisateur de l'API interne comme un autre.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.audit.models import AuditLog
from apps.authentication.models import UserRole
from apps.billing import services as billing_services
from apps.billing.models import Invoice, InvoiceLine, Payment
from apps.catalog import services as catalog_services
from apps.catalog.models import Category, Product, Unit
from apps.cooperatives.models import Cooperative
from apps.cooperatives.services import CooperativeRegistrationData, register_cooperative
from apps.inventory import services as inventory_services
from apps.inventory.models import StockLevel, StockMovement
from apps.members.models import Member
from apps.members.services import create_member
from apps.partners.models import Partner
from apps.partners.services import create_partner
from apps.purchases import services as purchases_services
from apps.purchases.models import PurchaseOrder, PurchaseOrderLine
from apps.sales import services as sales_services
from apps.sales.models import SalesOrder, SalesOrderLine
from apps.users.models import Invitation
from apps.warehouses.models import Warehouse
from apps.warehouses.services import create_warehouse

User = get_user_model()

DEMO_SLUG_HINT = "argane-sud-demo"
DEMO_PASSWORD = "Demo1234!"


class Command(BaseCommand):
    help = "Crée une coopérative de démonstration avec un jeu de données complet."

    def add_arguments(self, parser) -> None:  # noqa: ANN001
        parser.add_argument(
            "--reset", action="store_true",
            help="Supprime la coopérative de démo existante (et toutes ses données) avant de la recréer.",
        )

    def handle(self, *args, **options) -> None:
        if options["reset"]:
            existing = Cooperative.objects.filter(name="Coopérative Argane du Sud (Démo)").first()
            if existing is not None:
                self._delete_cooperative_deep(existing)
                self.stdout.write(self.style.WARNING("Ancienne coopérative de démo supprimée."))

        with transaction.atomic():
            cooperative, owner = self._create_cooperative_and_owner()
            admin, staff, accountant = self._create_team(cooperative)
            self._create_members(cooperative)
            customers, suppliers = self._create_partners(cooperative)
            units = self._create_units(cooperative)
            categories = self._create_categories(cooperative)
            products = self._create_products(cooperative, units, categories)
            warehouse = self._create_warehouse(cooperative)
            self._run_purchase_cycle(cooperative, admin, suppliers, warehouse, products)
            self._run_sales_cycle(cooperative, staff, customers, warehouse, products)

        self._print_summary(cooperative, owner, admin, staff, accountant)

    # --- Coopérative & équipe ---

    def _create_cooperative_and_owner(self):
        cooperative, owner = register_cooperative(
            CooperativeRegistrationData(
                cooperative_name="Coopérative Argane du Sud (Démo)",
                owner_email="owner@demo.ma",
                owner_password=DEMO_PASSWORD,
                owner_first_name="Fatima",
                owner_last_name="El Amrani",
            )
        )
        cooperative.legal_name = "Coopérative Argane du Sud SARL"
        cooperative.ice = "001234567000099"
        cooperative.rc_number = "RC-45231"
        cooperative.city = "Agadir"
        cooperative.address = "Route d'Essaouira, Km 12"
        cooperative.phone_number = "0528123456"
        cooperative.email = "contact@argane-sud-demo.ma"
        cooperative.save()
        self.stdout.write(self.style.SUCCESS(f"✓ Coopérative créée : {cooperative.name}"))
        return cooperative, owner

    def _create_team(self, cooperative: Cooperative):
        admin = User.objects.create_user(
            username="admin@demo.ma", email="admin@demo.ma", password=DEMO_PASSWORD,
            first_name="Karim", last_name="Bennani", cooperative=cooperative, role=UserRole.ADMIN,
        )
        staff = User.objects.create_user(
            username="staff@demo.ma", email="staff@demo.ma", password=DEMO_PASSWORD,
            first_name="Yassine", last_name="Ouazzani", cooperative=cooperative, role=UserRole.STAFF,
        )
        accountant = User.objects.create_user(
            username="accountant@demo.ma", email="accountant@demo.ma", password=DEMO_PASSWORD,
            first_name="Salma", last_name="Idrissi", cooperative=cooperative, role=UserRole.ACCOUNTANT,
        )
        self.stdout.write(self.style.SUCCESS("✓ Équipe créée (admin, staff, accountant)"))
        return admin, staff, accountant

    # --- Référentiels ---

    def _create_members(self, cooperative: Cooperative) -> None:
        members_data = [
            ("Ahmed", "Ouazzani", "0661234567"), ("Khadija", "Bensaid", "0662345678"),
            ("Mohammed", "Alaoui", "0663456789"), ("Zineb", "Chraibi", "0664567890"),
            ("Hassan", "Fassi", "0665678901"),
        ]
        for first_name, last_name, phone in members_data:
            create_member(cooperative=cooperative, first_name=first_name, last_name=last_name, phone_number=phone)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(members_data)} membres créés"))

    def _create_partners(self, cooperative: Cooperative):
        customers = [
            create_partner(
                cooperative=cooperative, is_customer=True, is_supplier=False,
                name="Épicerie Fine Al Baraka", phone_number="0522111222", city="Casablanca",
                payment_terms_days=30, credit_limit=Decimal("15000"),
            ),
            create_partner(
                cooperative=cooperative, is_customer=True, is_supplier=False,
                name="Boutique Souk Argane Export", phone_number="0524333444", city="Marrakech",
                payment_terms_days=15, credit_limit=Decimal("8000"),
            ),
        ]
        suppliers = [
            create_partner(
                cooperative=cooperative, is_customer=False, is_supplier=True,
                name="Fournisseur Emballages Sud", phone_number="0528555666", city="Agadir",
            ),
        ]
        self.stdout.write(self.style.SUCCESS(f"✓ {len(customers)} clients et {len(suppliers)} fournisseur(s) créés"))
        return customers, suppliers

    def _create_units(self, cooperative: Cooperative):
        return {
            "kg": Unit.objects.create(cooperative=cooperative, name="Kilogramme", symbol="kg", unit_type="weight"),
            "l": Unit.objects.create(cooperative=cooperative, name="Litre", symbol="L", unit_type="volume"),
            "pc": Unit.objects.create(cooperative=cooperative, name="Pièce", symbol="pc", unit_type="count"),
        }

    def _create_categories(self, cooperative: Cooperative):
        return {
            "huiles": Category.objects.create(cooperative=cooperative, name={"fr": "Huiles", "ar": "الزيوت"}),
            "cosmetique": Category.objects.create(cooperative=cooperative, name={"fr": "Cosmétique", "ar": "مستحضرات التجميل"}),
        }

    def _create_products(self, cooperative: Cooperative, units: dict, categories: dict):
        products = {
            "huile_culinaire": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Huile d'argane culinaire", "ar": "زيت الأركان الغذائي"},
                unit=units["l"], category=categories["huiles"],
                reference_purchase_price=Decimal("180"), reference_sale_price=Decimal("280"),
                minimum_stock_threshold=Decimal("20"),
            ),
            "huile_cosmetique": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Huile d'argane cosmétique", "ar": "زيت الأركان التجميلي"},
                unit=units["l"], category=categories["cosmetique"],
                reference_purchase_price=Decimal("220"), reference_sale_price=Decimal("350"),
                minimum_stock_threshold=Decimal("15"),
            ),
            "savon": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Savon noir à l'argane", "ar": "الصابون الأسود بالأركان"},
                unit=units["pc"], category=categories["cosmetique"],
                reference_purchase_price=Decimal("12"), reference_sale_price=Decimal("25"),
                minimum_stock_threshold=Decimal("50"),
            ),
        }
        self.stdout.write(self.style.SUCCESS(f"✓ {len(products)} produits créés"))
        return products

    def _create_warehouse(self, cooperative: Cooperative):
        warehouse = create_warehouse(cooperative=cooperative, name="Entrepôt Principal Agadir", city="Agadir")
        self.stdout.write(self.style.SUCCESS("✓ Entrepôt créé (défini par défaut)"))
        return warehouse

    # --- Cycle Achats -> Stock ---

    def _run_purchase_cycle(self, cooperative, admin, suppliers, warehouse, products) -> None:
        order = purchases_services.create_purchase_order(
            cooperative=cooperative, supplier=suppliers[0], warehouse=warehouse, actor=admin,
            order_date=date.today() - timedelta(days=10),
            lines=[
                {"product": products["huile_culinaire"], "quantity_ordered": Decimal("100"), "unit_price": Decimal("175")},
                {"product": products["savon"], "quantity_ordered": Decimal("200"), "unit_price": Decimal("11")},
            ],
        )
        purchases_services.confirm_purchase_order(order=order, actor=admin)
        purchases_services.record_purchase_receipt(
            order=order, actor=admin,
            receipts=[{"line_id": line.id, "quantity": line.quantity_ordered} for line in order.lines.all()],
        )

        # Un peu de stock supplémentaire directement en entrée (ex: production propre de la coopérative).
        inventory_services.record_stock_in(
            product=products["huile_cosmetique"], warehouse=warehouse, quantity=Decimal("40"),
            actor=admin, reason="initial", reference="STOCK-INITIAL",
        )
        self.stdout.write(self.style.SUCCESS("✓ Commande d'achat reçue, stock initial constitué"))

    # --- Cycle Ventes -> Facturation ---

    def _run_sales_cycle(self, cooperative, staff, customers, warehouse, products) -> None:
        order = sales_services.create_sales_order(
            cooperative=cooperative, customer=customers[0], warehouse=warehouse, actor=staff,
            order_date=date.today() - timedelta(days=5),
            lines=[
                {"product": products["huile_culinaire"], "quantity_ordered": Decimal("20"), "unit_price": Decimal("280")},
                {"product": products["savon"], "quantity_ordered": Decimal("50"), "unit_price": Decimal("25")},
            ],
        )
        sales_services.confirm_sales_order(order=order, actor=staff)
        sales_services.record_sales_delivery(
            order=order, actor=staff,
            deliveries=[{"line_id": line.id, "quantity": line.quantity_ordered} for line in order.lines.all()],
        )

        invoice = billing_services.generate_invoice_from_sales_order(
            order=order, actor=staff, issue_date=date.today() - timedelta(days=4),
        )
        billing_services.issue_invoice(invoice=invoice, actor=staff)
        billing_services.record_payment(
            invoice=invoice, amount=invoice.total_amount / 2, payment_date=date.today() - timedelta(days=1),
            actor=staff, payment_method="bank_transfer", reference="VIR-DEMO-001",
        )

        # Une deuxième commande, encore non livrée, pour peupler les statuts "en cours".
        sales_services.create_sales_order(
            cooperative=cooperative, customer=customers[1], warehouse=warehouse, actor=staff,
            order_date=date.today(),
            lines=[{"product": products["huile_cosmetique"], "quantity_ordered": Decimal("10"), "unit_price": Decimal("350")}],
        )
        self.stdout.write(self.style.SUCCESS("✓ Vente livrée et facturée (paiement partiel), 2e commande en brouillon"))

    # --- Résumé final ---

    @staticmethod
    def _delete_cooperative_deep(cooperative: Cooperative) -> None:
        """
        Une simple suppression en cascade de `Cooperative` échoue : plusieurs
        modèles utilisent volontairement `on_delete=PROTECT` vers Product/
        Warehouse/Partner (empêcher la suppression accidentelle d'un produit
        encore référencé par un mouvement de stock ou une facture — une
        garantie d'intégrité posée dès les Epics 8 à 11).

        Django ne devine pas tout seul qu'il peut supprimer les deux côtés
        d'une relation PROTECT dans la même opération : il faut donc
        supprimer explicitement dans l'ordre inverse des dépendances,
        des lignes de détail vers les référentiels.
        """
        Payment.objects.filter(cooperative=cooperative).delete()
        InvoiceLine.objects.filter(cooperative=cooperative).delete()
        Invoice.objects.filter(cooperative=cooperative).delete()
        SalesOrderLine.objects.filter(cooperative=cooperative).delete()
        SalesOrder.objects.filter(cooperative=cooperative).delete()
        PurchaseOrderLine.objects.filter(cooperative=cooperative).delete()
        PurchaseOrder.objects.filter(cooperative=cooperative).delete()
        StockMovement.objects.filter(cooperative=cooperative).delete()
        StockLevel.objects.filter(cooperative=cooperative).delete()
        Product.all_objects.filter(cooperative=cooperative).delete()
        Category.objects.filter(cooperative=cooperative).delete()
        Unit.objects.filter(cooperative=cooperative).delete()
        Warehouse.all_objects.filter(cooperative=cooperative).delete()
        Partner.all_objects.filter(cooperative=cooperative).delete()
        Member.all_objects.filter(cooperative=cooperative).delete()
        Invitation.objects.filter(cooperative=cooperative).delete()
        AuditLog.objects.filter(cooperative=cooperative).delete()
        User.objects.filter(cooperative=cooperative).delete()
        cooperative.delete()

    def _print_summary(self, cooperative, owner, admin, staff, accountant) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS(f"  Coopérative de démo prête : {cooperative.name}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write("  Comptes de connexion (mot de passe identique pour tous) :")
        self.stdout.write(f"    Mot de passe : {DEMO_PASSWORD}")
        self.stdout.write("")
        for user in (owner, admin, staff, accountant):
            self.stdout.write(f"    {user.role:<12} {user.email}")
        self.stdout.write("")
        self.stdout.write("  Connecte-toi sur http://localhost:5173 avec owner@demo.ma pour voir le dashboard complet.")
        self.stdout.write(self.style.SUCCESS("=" * 60))
