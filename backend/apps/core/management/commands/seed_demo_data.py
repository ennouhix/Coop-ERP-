"""
Commande de seed : crée une coopérative de démonstration avec un jeu de
données complet et cohérent — pas juste des lignes vides, mais un vrai
cycle métier déjà exécuté (achats reçus, ventes livrées, factures à tous
les statuts, stock multi-entrepôts, comptabilité PCM et écritures).

Usage :
    python manage.py seed_demo_data
    python manage.py seed_demo_data --reset   # supprime la démo existante avant de la recréer

Réutilise exclusivement les services métier déjà construits (jamais de
création directe de modèle qui contournerait les règles métier) — cette
commande est un utilisateur de l'API interne comme un autre. Seule
exception : les comptes/journaux PCM (plan comptable marocain), qui n'ont
pas de service dédié et sont créés directement comme dans `load_pcm`.
"""
# ruff: noqa: E501 — les lignes de données (noms FR/AR, lignes de commande)
# dépassent naturellement 100 caractères ; on privilégie la lisibilité.
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounting.management.commands.load_pcm import DEFAULT_JOURNALS, PCM_ACCOUNTS
from apps.accounting.models import Account, AccountingEntry, AccountingEntryLine, Journal
from apps.accounting.services import create_accounting_entry, post_entry
from apps.audit.models import AuditLog
from apps.authentication.models import UserRole
from apps.billing import services as billing_services
from apps.billing.models import Invoice, InvoiceLine, Payment, PaymentMethod
from apps.catalog import services as catalog_services
from apps.catalog.models import Category, Product, Unit
from apps.cooperatives.models import Cooperative
from apps.cooperatives.services import CooperativeRegistrationData, register_cooperative
from apps.inventory import services as inventory_services
from apps.inventory.models import StockLevel, StockMovement
from apps.members.models import Member, MemberStatus
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
    help = "Crée une coopérative de démonstration avec un jeu de données complet et riche."

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
            warehouses = self._create_warehouses(cooperative)
            accounts, journals = self._load_pcm(cooperative)
            self._run_purchase_cycles(cooperative, admin, suppliers, warehouses, products)
            self._run_stock_cycles(cooperative, admin, warehouses, products)
            orders = self._run_sales_cycles(cooperative, staff, customers, warehouses, products)
            self._run_invoice_cycles(cooperative, staff, customers, products, orders)
            self._run_accounting_cycles(cooperative, accountant, accounts, journals)

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
        self.stdout.write(self.style.SUCCESS("✓ Équipe créée (owner, admin, staff, accountant)"))
        return admin, staff, accountant

    # --- Référentiels ---

    def _create_members(self, cooperative: Cooperative) -> None:
        members_data = [
            ("Ahmed", "Ouazzani", "0661234567", "AB123456", "Agadir", MemberStatus.ACTIVE, 10),
            ("Khadija", "Bensaid", "0662345678", "CD234567", "Tiznit", MemberStatus.ACTIVE, 8),
            ("Mohammed", "Alaoui", "0663456789", "EF345678", "Essaouira", MemberStatus.ACTIVE, 12),
            ("Zineb", "Chraibi", "0664567890", "GH456789", "Taroudant", MemberStatus.ACTIVE, 6),
            ("Hassan", "Fassi", "0665678901", "IJ567890", "Agadir", MemberStatus.ACTIVE, 10),
            ("Latifa", "Berrada", "0666789012", "KL678901", "Tiznit", MemberStatus.ACTIVE, 15),
            ("Rachid", "Tazi", "0667890123", "MN789012", "Agadir", MemberStatus.ACTIVE, 5),
            ("Amina", "Bouzid", "0668901234", "OP890123", "Sidi Ifni", MemberStatus.ACTIVE, 7),
            ("Youssef", "El Kettani", "0669012345", "QR901234", "Agadir", MemberStatus.ACTIVE, 10),
            ("Nadia", "Sefrioui", "0670123456", "RS012345", "Essaouira", MemberStatus.SUSPENDED, 4),
            ("Omar", "Benjelloun", "0671234567", "ST123456", "Tiznit", MemberStatus.ACTIVE, 9),
            ("Samira", "Lahlou", "0672345678", "TU234567", "Agadir", MemberStatus.ACTIVE, 8),
            ("Khalid", "Naciri", "0673456789", "UV345678", "Taroudant", MemberStatus.ACTIVE, 6),
            ("Houda", "El Amrani", "0674567890", "VW456789", "Agadir", MemberStatus.ACTIVE, 11),
            ("Said", "Mernissi", "0675678901", "WX567890", "Agadir", MemberStatus.INACTIVE, 3),
            ("Malika", "Idrissi", "0676789012", "XY678901", "Tiznit", MemberStatus.ACTIVE, 8),
            ("Driss", "Boumediene", "0677890123", "YZ789012", "Agadir", MemberStatus.SUSPENDED, 2),
            ("Fatima Zahra", "Lamrani", "0678901234", "ZA890123", "Sidi Ifni", MemberStatus.INACTIVE, 5),
        ]
        for index, (first_name, last_name, phone, cin, city, status, shares) in enumerate(members_data):
            create_member(
                cooperative=cooperative, first_name=first_name, last_name=last_name,
                phone_number=phone, cin=cin, city=city, status=status,
                shares_count=shares, join_date=date.today() - timedelta(days=index * 25 + 30),
            )
        self.stdout.write(self.style.SUCCESS(f"✓ {len(members_data)} membres créés"))

    def _create_partners(self, cooperative: Cooperative):
        customers = [
            create_partner(
                cooperative=cooperative, is_customer=True, is_supplier=False,
                name="Épicerie Fine Al Baraka", phone_number="0522111222", city="Casablanca",
                payment_terms_days=30, credit_limit=Decimal("60000"),
            ),
            create_partner(
                cooperative=cooperative, is_customer=True, is_supplier=False,
                name="Boutique Souk Argane Export", phone_number="0524333444", city="Marrakech",
                payment_terms_days=15, credit_limit=Decimal("40000"),
            ),
            create_partner(
                cooperative=cooperative, is_customer=True, is_supplier=False,
                name="Coopérative Rurale Tafraout", phone_number="0528555777", city="Tafraout",
                payment_terms_days=45, credit_limit=Decimal("30000"),
            ),
            create_partner(
                cooperative=cooperative, is_customer=True, is_supplier=False,
                name="Hamam & Cosmétique Atlas", phone_number="0528444888", city="Agadir",
                payment_terms_days=30, credit_limit=Decimal("25000"),
            ),
            create_partner(
                cooperative=cooperative, is_customer=True, is_supplier=False,
                name="Suprême Cadeaux Souss", phone_number="0528333999", city="Agadir",
                payment_terms_days=60, credit_limit=Decimal("35000"),
            ),
            create_partner(
                cooperative=cooperative, is_customer=True, is_supplier=False,
                name="Marché Municipal Taroudant", phone_number="0528233000", city="Taroudant",
                payment_terms_days=30, credit_limit=Decimal("20000"),
            ),
        ]
        suppliers = [
            create_partner(
                cooperative=cooperative, is_customer=False, is_supplier=True,
                name="Fournisseur Emballages Sud", phone_number="0528555666", city="Agadir",
            ),
            create_partner(
                cooperative=cooperative, is_customer=False, is_supplier=True,
                name="Bouteilles Atlas Glass", phone_number="0522555111", city="Casablanca",
            ),
            create_partner(
                cooperative=cooperative, is_customer=False, is_supplier=True,
                name="Coopérative Productrice Taliouine", phone_number="0528666222", city="Taliouine",
            ),
            create_partner(
                cooperative=cooperative, is_customer=False, is_supplier=True,
                name="Transport & Logistique Souss", phone_number="0528777333", city="Agadir",
            ),
        ]
        self.stdout.write(
            self.style.SUCCESS(f"✓ {len(customers)} clients et {len(suppliers)} fournisseur(s) créés")
        )
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
            "savons": Category.objects.create(cooperative=cooperative, name={"fr": "Savons", "ar": "الصابون"}),
            "terroir": Category.objects.create(cooperative=cooperative, name={"fr": "Produits du terroir", "ar": "منتوجات محلية"}),
            "epicerie": Category.objects.create(cooperative=cooperative, name={"fr": "Épicerie fine", "ar": "بقالة راقية"}),
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
                unit=units["l"], category=categories["huiles"],
                reference_purchase_price=Decimal("220"), reference_sale_price=Decimal("350"),
                minimum_stock_threshold=Decimal("15"),
            ),
            "huile_barbarie": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Huile de figue de barbarie", "ar": "زيت التين الشوكي"},
                unit=units["l"], category=categories["huiles"],
                reference_purchase_price=Decimal("300"), reference_sale_price=Decimal("450"),
                minimum_stock_threshold=Decimal("10"),
            ),
            "savon_noir": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Savon noir à l'argane", "ar": "الصابون الأسود بالأركان"},
                unit=units["pc"], category=categories["savons"],
                reference_purchase_price=Decimal("12"), reference_sale_price=Decimal("25"),
                minimum_stock_threshold=Decimal("50"),
            ),
            "savon_argane": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Savon à l'argane", "ar": "صابون الأركان"},
                unit=units["pc"], category=categories["savons"],
                reference_purchase_price=Decimal("18"), reference_sale_price=Decimal("35"),
                minimum_stock_threshold=Decimal("40"),
            ),
            "savon_lait": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Savon au lait de chèvre", "ar": "صابون حليب الماعز"},
                unit=units["pc"], category=categories["savons"],
                reference_purchase_price=Decimal("15"), reference_sale_price=Decimal("28"),
                minimum_stock_threshold=Decimal("40"),
            ),
            "amlou": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Amlou traditionnel", "ar": "أملو تقليدي"},
                unit=units["kg"], category=categories["terroir"],
                reference_purchase_price=Decimal("90"), reference_sale_price=Decimal("150"),
                minimum_stock_threshold=Decimal("25"),
            ),
            "creme": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Crème hydratante à l'argane", "ar": "كريم مرطب بالأركان"},
                unit=units["pc"], category=categories["cosmetique"],
                reference_purchase_price=Decimal("45"), reference_sale_price=Decimal("85"),
                minimum_stock_threshold=Decimal("20"),
            ),
            "the": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Thé à la menthe", "ar": "شاي النعناع"},
                unit=units["kg"], category=categories["epicerie"],
                reference_purchase_price=Decimal("60"), reference_sale_price=Decimal("110"),
                minimum_stock_threshold=Decimal("30"),
            ),
            "epices": catalog_services.create_product(
                cooperative=cooperative, name={"fr": "Mélange d'épices artisanales", "ar": "خليط التوابل التقليدية"},
                unit=units["kg"], category=categories["epicerie"],
                reference_purchase_price=Decimal("40"), reference_sale_price=Decimal("75"),
                minimum_stock_threshold=Decimal("30"),
            ),
        }
        self.stdout.write(self.style.SUCCESS(f"✓ {len(products)} produits créés"))
        return products

    def _create_warehouses(self, cooperative: Cooperative):
        main = create_warehouse(cooperative=cooperative, name="Entrepôt Principal Agadir", city="Agadir")
        secondary = create_warehouse(cooperative=cooperative, name="Dépôt Tiznit", city="Tiznit")
        self.stdout.write(self.style.SUCCESS("✓ 2 entrepôts créés (Agadir par défaut + Dépôt Tiznit)"))
        return {"agadir": main, "tiznit": secondary}

    def _load_pcm(self, cooperative: Cooperative):
        """Charge le plan comptable marocain + journaux (comme `load_pcm`)."""
        code_to_account: dict[str, Account] = {}
        for acc_data in PCM_ACCOUNTS:
            parent = code_to_account.get(acc_data["parent_code"]) if acc_data["parent_code"] else None
            account, _ = Account.all_objects.get_or_create(
                cooperative=cooperative, code=acc_data["code"],
                defaults={
                    "name": {"fr": acc_data["fr"], "ar": acc_data["ar"]},
                    "account_type": acc_data["type"],
                    "parent": parent,
                    "is_system": True,
                    "is_active": True,
                },
            )
            code_to_account[acc_data["code"]] = account
        journals = {
            jdata["code"]: Journal.all_objects.get_or_create(
                cooperative=cooperative, code=jdata["code"],
                defaults={
                    "name": {"fr": jdata["fr"], "ar": jdata["ar"]},
                    "journal_type": jdata["type"],
                    "is_active": True,
                },
            )[0]
            for jdata in DEFAULT_JOURNALS
        }
        self.stdout.write(
            self.style.SUCCESS(f"✓ PCM chargé ({len(code_to_account)} comptes, {len(journals)} journaux)")
        )
        return code_to_account, journals

    # --- Achats -> Stock ---

    def _create_purchase(self, cooperative, supplier, warehouse, actor, order_date, lines):
        order = purchases_services.create_purchase_order(
            cooperative=cooperative, supplier=supplier, warehouse=warehouse, actor=actor,
            order_date=order_date, lines=lines,
        )
        return order

    def _receive_full(self, order, actor) -> None:
        purchases_services.confirm_purchase_order(order=order, actor=actor)
        purchases_services.record_purchase_receipt(
            order=order, actor=actor,
            receipts=[{"line_id": line.id, "quantity": line.quantity_ordered} for line in order.lines.all()],
        )

    def _run_purchase_cycles(self, cooperative, admin, suppliers, warehouses, products) -> None:
        d = date.today()

        # 1) Commandes entièrement réceptionnées (les deux fournisseurs principaux).
        order_a = self._create_purchase(
            cooperative, suppliers[0], warehouses["agadir"], admin, d - timedelta(days=45),
            lines=[
                {"product": products["huile_culinaire"], "quantity_ordered": Decimal("100"), "unit_price": Decimal("175")},
                {"product": products["savon_noir"], "quantity_ordered": Decimal("200"), "unit_price": Decimal("11")},
                {"product": products["amlou"], "quantity_ordered": Decimal("60"), "unit_price": Decimal("85")},
                {"product": products["savon_argane"], "quantity_ordered": Decimal("150"), "unit_price": Decimal("17")},
            ],
        )
        self._receive_full(order_a, admin)

        order_b = self._create_purchase(
            cooperative, suppliers[2], warehouses["agadir"], admin, d - timedelta(days=20),
            lines=[
                {"product": products["huile_cosmetique"], "quantity_ordered": Decimal("60"), "unit_price": Decimal("210")},
                {"product": products["creme"], "quantity_ordered": Decimal("100"), "unit_price": Decimal("42")},
                {"product": products["huile_barbarie"], "quantity_ordered": Decimal("30"), "unit_price": Decimal("290")},
                {"product": products["savon_lait"], "quantity_ordered": Decimal("150"), "unit_price": Decimal("14")},
            ],
        )
        self._receive_full(order_b, admin)

        # 2) Commande confirmée, non encore réceptionnée.
        order_c = self._create_purchase(
            cooperative, suppliers[1], warehouses["agadir"], admin, d - timedelta(days=5),
            lines=[
                {"product": products["huile_culinaire"], "quantity_ordered": Decimal("50"), "unit_price": Decimal("175")},
                {"product": products["huile_cosmetique"], "quantity_ordered": Decimal("40"), "unit_price": Decimal("215")},
            ],
        )
        purchases_services.confirm_purchase_order(order=order_c, actor=admin)

        # 3) Commande partiellement réceptionnée (dépôt Tiznit).
        order_d = self._create_purchase(
            cooperative, suppliers[2], warehouses["tiznit"], admin, d - timedelta(days=12),
            lines=[
                {"product": products["amlou"], "quantity_ordered": Decimal("40"), "unit_price": Decimal("88")},
                {"product": products["the"], "quantity_ordered": Decimal("80"), "unit_price": Decimal("55")},
                {"product": products["epices"], "quantity_ordered": Decimal("60"), "unit_price": Decimal("38")},
            ],
        )
        purchases_services.confirm_purchase_order(order=order_d, actor=admin)
        purchases_services.record_purchase_receipt(
            order=order_d, actor=admin,
            receipts=[
                {"line_id": line.id, "quantity": line.quantity_ordered / 2}
                for line in order_d.lines.all()
            ],
        )

        # 4) Brouillon et annulée.
        self._create_purchase(
            cooperative, suppliers[0], warehouses["agadir"], admin, d - timedelta(days=1),
            lines=[
                {"product": products["savon_argane"], "quantity_ordered": Decimal("80"), "unit_price": Decimal("17")},
                {"product": products["savon_lait"], "quantity_ordered": Decimal("100"), "unit_price": Decimal("14")},
            ],
        )
        order_f = self._create_purchase(
            cooperative, suppliers[1], warehouses["agadir"], admin, d - timedelta(days=30),
            lines=[{"product": products["huile_barbarie"], "quantity_ordered": Decimal("20"), "unit_price": Decimal("295")}],
        )
        purchases_services.confirm_purchase_order(order=order_f, actor=admin)
        purchases_services.cancel_purchase_order(order=order_f, actor=admin)

        self.stdout.write(self.style.SUCCESS("✓ Cycle achats : reçue ×2, confirmée, partielle, brouillon, annulée"))

    def _run_stock_cycles(self, cooperative, admin, warehouses, products) -> None:
        # Production propre de la coopérative (entrée).
        inventory_services.record_stock_in(
            product=products["huile_cosmetique"], warehouse=warehouses["agadir"], quantity=Decimal("40"),
            actor=admin, reason="initial", reference="PROD-INTERNE-001",
        )
        # Transfert inter-entrepôts Agadir -> Tiznit.
        inventory_services.record_stock_transfer(
            product=products["huile_culinaire"], from_warehouse=warehouses["agadir"],
            to_warehouse=warehouses["tiznit"], quantity=Decimal("20"),
            actor=admin, reference="TRF-001",
        )
        # Pertes / casse.
        inventory_services.record_stock_out(
            product=products["savon_lait"], warehouse=warehouses["agadir"], quantity=Decimal("5"),
            actor=admin, reason="loss", reference="PERTE-001",
        )
        # Ajustements d'inventaire (=> stock bas signalé).
        inventory_services.record_stock_out(
            product=products["savon_argane"], warehouse=warehouses["agadir"], quantity=Decimal("15"),
            actor=admin, reason="adjustment", reference="AJUST-001",
        )
        inventory_services.record_stock_out(
            product=products["epices"], warehouse=warehouses["tiznit"], quantity=Decimal("5"),
            actor=admin, reason="adjustment", reference="AJUST-002",
        )
        # Un mouvement de sortie récent pour peupler le filtre "raison".
        inventory_services.record_stock_out(
            product=products["amlou"], warehouse=warehouses["agadir"], quantity=Decimal("3"),
            actor=admin, reason="return_supplier", reference="RET-001",
        )
        self.stdout.write(self.style.SUCCESS("✓ Stock : entrée, transfert, perte, ajustements, retour"))

    # --- Ventes -> Livraisons ---

    def _create_sales(self, cooperative, staff, customer, warehouse, products, order_date, lines):
        return sales_services.create_sales_order(
            cooperative=cooperative, customer=customer, warehouse=warehouse, actor=staff,
            order_date=order_date, lines=lines,
        )

    def _deliver_full(self, order, actor) -> None:
        sales_services.confirm_sales_order(order=order, actor=actor)
        sales_services.record_sales_delivery(
            order=order, actor=actor,
            deliveries=[{"line_id": line.id, "quantity": line.quantity_ordered} for line in order.lines.all()],
        )

    def _run_sales_cycles(self, cooperative, staff, customers, warehouses, products):
        d = date.today()
        orders = {}

        # Livrées (seront facturées dans le cycle factures).
        orders["so1"] = self._create_sales(
            cooperative, staff, customers[0], warehouses["agadir"], products, d - timedelta(days=8),
            lines=[
                {"product": products["huile_culinaire"], "quantity_ordered": Decimal("20"), "unit_price": Decimal("280")},
                {"product": products["savon_noir"], "quantity_ordered": Decimal("50"), "unit_price": Decimal("25")},
                {"product": products["amlou"], "quantity_ordered": Decimal("15"), "unit_price": Decimal("150")},
            ],
        )
        self._deliver_full(orders["so1"], staff)

        orders["so2"] = self._create_sales(
            cooperative, staff, customers[1], warehouses["agadir"], products, d - timedelta(days=15),
            lines=[
                {"product": products["huile_cosmetique"], "quantity_ordered": Decimal("15"), "unit_price": Decimal("350")},
                {"product": products["creme"], "quantity_ordered": Decimal("30"), "unit_price": Decimal("85")},
                {"product": products["savon_argane"], "quantity_ordered": Decimal("40"), "unit_price": Decimal("35")},
            ],
        )
        self._deliver_full(orders["so2"], staff)

        orders["so3"] = self._create_sales(
            cooperative, staff, customers[3], warehouses["agadir"], products, d - timedelta(days=30),
            lines=[
                {"product": products["savon_argane"], "quantity_ordered": Decimal("60"), "unit_price": Decimal("35")},
                {"product": products["savon_noir"], "quantity_ordered": Decimal("80"), "unit_price": Decimal("25")},
                {"product": products["savon_lait"], "quantity_ordered": Decimal("40"), "unit_price": Decimal("28")},
            ],
        )
        self._deliver_full(orders["so3"], staff)

        # Partiellement livrée (facturée sur les quantités livrées uniquement).
        orders["so7"] = self._create_sales(
            cooperative, staff, customers[0], warehouses["agadir"], products, d - timedelta(days=10),
            lines=[
                {"product": products["creme"], "quantity_ordered": Decimal("40"), "unit_price": Decimal("85")},
                {"product": products["savon_lait"], "quantity_ordered": Decimal("30"), "unit_price": Decimal("28")},
            ],
        )
        sales_services.confirm_sales_order(order=orders["so7"], actor=staff)
        sales_services.record_sales_delivery(
            order=orders["so7"], actor=staff,
            deliveries=[
                {"line_id": orders["so7"].lines.all()[0].id, "quantity": Decimal("20")},
                {"line_id": orders["so7"].lines.all()[1].id, "quantity": Decimal("15")},
            ],
        )

        # Confirmée, non livrée.
        orders["so4"] = self._create_sales(
            cooperative, staff, customers[4], warehouses["agadir"], products, d - timedelta(days=3),
            lines=[
                {"product": products["huile_culinaire"], "quantity_ordered": Decimal("10"), "unit_price": Decimal("285")},
                {"product": products["amlou"], "quantity_ordered": Decimal("10"), "unit_price": Decimal("150")},
            ],
        )
        sales_services.confirm_sales_order(order=orders["so4"], actor=staff)

        # Brouillon.
        self._create_sales(
            cooperative, staff, customers[5], warehouses["agadir"], products, d - timedelta(days=1),
            lines=[
                {"product": products["huile_cosmetique"], "quantity_ordered": Decimal("8"), "unit_price": Decimal("350")},
                {"product": products["creme"], "quantity_ordered": Decimal("10"), "unit_price": Decimal("85")},
            ],
        )

        # Annulée.
        orders["so6"] = self._create_sales(
            cooperative, staff, customers[1], warehouses["agadir"], products, d - timedelta(days=25),
            lines=[{"product": products["huile_barbarie"], "quantity_ordered": Decimal("5"), "unit_price": Decimal("450")}],
        )
        sales_services.confirm_sales_order(order=orders["so6"], actor=staff)
        sales_services.cancel_sales_order(order=orders["so6"], actor=staff)

        self.stdout.write(self.style.SUCCESS("✓ Ventes : livrée ×3, partielle, confirmée, brouillon, annulée"))
        return orders

    # --- Factures & paiements ---

    def _invoice_from_order(self, order, actor, issue_date, due_date=None):
        invoice = billing_services.generate_invoice_from_sales_order(
            order=order, actor=actor, issue_date=issue_date, due_date=due_date,
        )
        billing_services.issue_invoice(invoice=invoice, actor=actor)
        return invoice

    def _manual_invoice(self, cooperative, customer, actor, issue_date, lines, due_date=None):
        invoice = billing_services.create_manual_invoice(
            cooperative=cooperative, customer=customer, actor=actor,
            issue_date=issue_date, due_date=due_date, lines=lines,
        )
        return invoice

    def _run_invoice_cycles(self, cooperative, staff, customers, products, orders) -> None:
        d = date.today()

        # 1) Factures émises depuis les commandes livrées.
        #    Facture A — partiellement réglée (virement).
        invoice_a = self._invoice_from_order(
            orders["so3"], staff, d - timedelta(days=29),
        )
        #    Facture B — entièrement réglée (espèces).
        invoice_b = self._invoice_from_order(
            orders["so2"], staff, d - timedelta(days=14),
        )
        #    Facture C — échue et impayée (encours client en retard).
        self._invoice_from_order(
            orders["so1"], staff, d - timedelta(days=7), due_date=d - timedelta(days=5),
        )
        #    Facture D — émise à l'échéance, impayée mais pas en retard.
        self._invoice_from_order(
            orders["so7"], staff, d - timedelta(days=6),
        )

        # 2) Paiements.
        billing_services.record_payment(
            invoice=invoice_a, amount=invoice_a.total_amount / 2,
            payment_date=d - timedelta(days=2), actor=staff,
            payment_method=PaymentMethod.BANK_TRANSFER, reference="VIR-DEMO-001",
        )
        billing_services.record_payment(
            invoice=invoice_b, amount=invoice_b.total_amount,
            payment_date=d - timedelta(days=3), actor=staff,
            payment_method=PaymentMethod.CASH, reference="ESP-DEMO-001",
        )

        # 3) Facture manuelle partiellement payée.
        manual_partial = self._manual_invoice(
            cooperative, customers[5], staff, d - timedelta(days=10),
            lines=[
                {"product": products["huile_culinaire"], "quantity": Decimal("5"), "unit_price": Decimal("285")},
                {"product": products["savon_noir"], "quantity": Decimal("20"), "unit_price": Decimal("25")},
            ],
            due_date=d + timedelta(days=20),
        )
        billing_services.issue_invoice(invoice=manual_partial, actor=staff)
        billing_services.record_payment(
            invoice=manual_partial, amount=Decimal("1000"),
            payment_date=d - timedelta(days=1), actor=staff,
            payment_method=PaymentMethod.CASH, reference="ESP-DEMO-002",
        )

        # 4) Facture manuelle entièrement payée.
        manual_paid = self._manual_invoice(
            cooperative, customers[4], staff, d - timedelta(days=6),
            lines=[
                {"product": products["amlou"], "quantity": Decimal("8"), "unit_price": Decimal("155")},
                {"product": products["the"], "quantity": Decimal("5"), "unit_price": Decimal("110")},
            ],
            due_date=d + timedelta(days=30),
        )
        billing_services.issue_invoice(invoice=manual_paid, actor=staff)
        billing_services.record_payment(
            invoice=manual_paid, amount=manual_paid.total_amount,
            payment_date=d - timedelta(days=2), actor=staff,
            payment_method=PaymentMethod.CHECK, reference="CHQ-DEMO-001",
        )

        # 5) Brouillon et annulée.
        self._manual_invoice(
            cooperative, customers[3], staff, d - timedelta(days=2),
            lines=[
                {"product": products["savon_lait"], "quantity": Decimal("10"), "unit_price": Decimal("28")},
                {"product": products["creme"], "quantity": Decimal("5"), "unit_price": Decimal("85")},
            ],
        )
        cancelled = self._manual_invoice(
            cooperative, customers[5], staff, d - timedelta(days=20),
            lines=[{"product": products["savon_noir"], "quantity": Decimal("10"), "unit_price": Decimal("25")}],
        )
        billing_services.issue_invoice(invoice=cancelled, actor=staff)
        billing_services.cancel_invoice(invoice=cancelled, actor=staff)

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Factures : {Invoice.objects.filter(cooperative=cooperative).count()} créées "
                "(payée, partielle, en retard, brouillon, annulée)"
            )
        )

    # --- Comptabilité ---

    def _account(self, accounts: dict, code: str) -> Account:
        return accounts[code]

    def _run_accounting_cycles(self, cooperative, accountant, accounts, journals) -> None:
        d = date.today()

        def entry(journal_code: str, entry_date, description, pairs) -> AccountingEntry:
            """pairs : liste de (code_compte, débit, crédit) — chaque écriture est équilibrée."""
            lines_data = [
                {
                    "account": self._account(accounts, code),
                    "label": description,
                    "debit": Decimal(str(debit)),
                    "credit": Decimal(str(credit)),
                }
                for code, debit, credit in pairs
            ]
            return create_accounting_entry(
                cooperative=cooperative, journal=journals[journal_code], entry_date=entry_date,
                description=description, lines_data=lines_data, actor=accountant,
            )

        # Apport en capital (validée, période antérieure).
        e1 = entry("OD", d - timedelta(days=50), "Apport en capital", [
            ("5141", 50000, 0), ("101", 0, 50000),
        ])
        post_entry(entry=e1, actor=accountant)
        # Achat de matières premières (validée, fournisseur à payer).
        e2 = entry("JA", d - timedelta(days=20), "Achat emballages et matières", [
            ("601", 12000, 0), ("401", 0, 12000),
        ])
        post_entry(entry=e2, actor=accountant)
        # Loyer local (validée, caisse).
        e3 = entry("CAI", d - timedelta(days=12), "Loyer local Agadir", [
            ("61", 3000, 0), ("5161", 0, 3000),
        ])
        post_entry(entry=e3, actor=accountant)
        # Subvention d'exploitation encaissée (validée, banque).
        e4 = entry("BQ", d - timedelta(days=8), "Subvention d'exploitation encaissée", [
            ("5141", 8000, 0), ("74", 0, 8000),
        ])
        post_entry(entry=e4, actor=accountant)
        # Provision (brouillon, non validée — visible dans le journal).
        entry("OD", d - timedelta(days=3), "Provision pour charges (à valider)", [
            ("63", 2000, 0), ("5161", 0, 2000),
        ])

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Comptabilité : {AccountingEntry.objects.filter(cooperative=cooperative).count()} écritures "
                "(dont celles générées automatiquement par les factures et paiements)"
            )
        )

    # --- Résumé final ---

    @staticmethod
    def _delete_cooperative_deep(cooperative: Cooperative) -> None:
        """
        Une simple suppression en cascade de `Cooperative` échoue : plusieurs
        modèles utilisent volontairement `on_delete=PROTECT` vers Product/
        Warehouse/Partner/Account (empêcher la suppression accidentelle d'un
        élément encore référencé). Il faut donc supprimer explicitement dans
        l'ordre inverse des dépendances, des lignes de détail vers les
        référentiels.
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
        AccountingEntryLine.objects.filter(cooperative=cooperative).delete()
        AccountingEntry.all_objects.filter(cooperative=cooperative).delete()
        # Account.parent est en PROTECT auto-référencé : on détache les
        # enfants avant de pouvoir supprimer la hiérarchie PCM.
        Account.all_objects.filter(cooperative=cooperative).update(parent=None)
        Account.all_objects.filter(cooperative=cooperative).delete()
        Journal.all_objects.filter(cooperative=cooperative).delete()
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
        counts = {
            "Membres": Member.all_objects.filter(cooperative=cooperative).count(),
            "Clients/Fournisseurs": Partner.all_objects.filter(cooperative=cooperative).count(),
            "Produits": Product.all_objects.filter(cooperative=cooperative).count(),
            "Entrepôts": Warehouse.all_objects.filter(cooperative=cooperative).count(),
            "Commandes d'achat": PurchaseOrder.objects.filter(cooperative=cooperative).count(),
            "Commandes de vente": SalesOrder.objects.filter(cooperative=cooperative).count(),
            "Factures": Invoice.objects.filter(cooperative=cooperative).count(),
            "Paiements": Payment.objects.filter(cooperative=cooperative).count(),
            "Mouvements de stock": StockMovement.objects.filter(cooperative=cooperative).count(),
            "Écritures comptables": AccountingEntry.objects.filter(cooperative=cooperative).count(),
        }

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS(f"  Coopérative de démo prête : {cooperative.name}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        for label, value in counts.items():
            self.stdout.write(f"  {label:<24} {value}")
        self.stdout.write("")
        self.stdout.write("  Comptes de connexion (mot de passe identique pour tous) :")
        self.stdout.write(f"    Mot de passe : {DEMO_PASSWORD}")
        self.stdout.write("")
        for user in (owner, admin, staff, accountant):
            self.stdout.write(f"    {user.role:<12} {user.email}")
        self.stdout.write("")
        self.stdout.write("  Connecte-toi sur http://localhost:5173 avec owner@demo.ma pour voir le dashboard complet.")
        self.stdout.write(self.style.SUCCESS("=" * 60))
