"""
Management command : charge le Plan Comptable Marocain (PCM) et les journaux
de base pour une coopérative donnée.

Usage :
    python manage.py load_pcm --cooperative-id <uuid>

Les comptes créés sont marqués is_system=True (non supprimables).
Les journaux créés couvrent les 5 types : ventes, achats, caisse, banque, OD.
"""

from __future__ import annotations

import uuid

from django.core.management.base import BaseCommand, CommandError

from apps.accounting.models import Account, AccountType, Journal, JournalType
from apps.cooperatives.models import Cooperative

PCM_ACCOUNTS: list[dict] = [
    # ---- Classe 1 : Financement permanent ----
    {
        "code": "1",
        "fr": "Comptes de financement permanent",
        "ar": "حسابات التمويل الدائم",
        "type": AccountType.EQUITY,
        "parent_code": None,
    },
    {
        "code": "10",
        "fr": "Capital et réserves",
        "ar": "رأس المال والاحتياطيات",
        "type": AccountType.EQUITY,
        "parent_code": "1",
    },
    {
        "code": "101",
        "fr": "Capital social ou personnel",
        "ar": "رأس المال الاجتماعي",
        "type": AccountType.EQUITY,
        "parent_code": "10",
    },
    {
        "code": "111",
        "fr": "Réserve légale",
        "ar": "الاحتياطي القانوني",
        "type": AccountType.EQUITY,
        "parent_code": "10",
    },
    {
        "code": "119",
        "fr": "Report à nouveau",
        "ar": "ترحيل من جديد",
        "type": AccountType.EQUITY,
        "parent_code": "10",
    },
    {
        "code": "14",
        "fr": "Dettes de financement",
        "ar": "ديون التمويل",
        "type": AccountType.LIABILITY,
        "parent_code": "1",
    },
    {
        "code": "141",
        "fr": "Emprunts auprès des établissements de crédit",
        "ar": "قروض من مؤسسات الائتمان",
        "type": AccountType.LIABILITY,
        "parent_code": "14",
    },
    {
        "code": "148",
        "fr": "Autres dettes de financement",
        "ar": "ديون التمويل الأخرى",
        "type": AccountType.LIABILITY,
        "parent_code": "14",
    },
    # ---- Classe 2 : Actif immobilisé ----
    {
        "code": "2",
        "fr": "Comptes d'actif immobilisé",
        "ar": "حسابات الأصول الثابتة",
        "type": AccountType.ASSET,
        "parent_code": None,
    },
    {
        "code": "21",
        "fr": "Immobilisations en non-valeurs",
        "ar": "الاستثمارات غير المادية",
        "type": AccountType.ASSET,
        "parent_code": "2",
    },
    {
        "code": "22",
        "fr": "Immobilisations incorporelles",
        "ar": "الأصول غير الملموسة",
        "type": AccountType.ASSET,
        "parent_code": "2",
    },
    {
        "code": "23",
        "fr": "Immobilisations corporelles",
        "ar": "الأصول المادية",
        "type": AccountType.ASSET,
        "parent_code": "2",
    },
    {
        "code": "28",
        "fr": "Amortissements des immobilisations",
        "ar": "إهلاك الأصول الثابتة",
        "type": AccountType.ASSET,
        "parent_code": "2",
    },
    # ---- Classe 3 : Actif circulant ----
    {
        "code": "3",
        "fr": "Comptes d'actif circulant",
        "ar": "حسابات الأصول المتداولة",
        "type": AccountType.ASSET,
        "parent_code": None,
    },
    {
        "code": "31",
        "fr": "Stocks de marchandises",
        "ar": "مخزون البضائع",
        "type": AccountType.ASSET,
        "parent_code": "3",
    },
    {
        "code": "32",
        "fr": "Stocks de matières et fournitures",
        "ar": "مخزون المواد والتوريدات",
        "type": AccountType.ASSET,
        "parent_code": "3",
    },
    {
        "code": "34",
        "fr": "Créances de l'actif circulant",
        "ar": "ذمم مدينة للأصول المتداولة",
        "type": AccountType.ASSET,
        "parent_code": "3",
    },
    {
        "code": "342",
        "fr": "Clients et comptes rattachés",
        "ar": "الزبائن والحسابات المرتبطة",
        "type": AccountType.ASSET,
        "parent_code": "34",
    },
    {
        "code": "345",
        "fr": "État — TVA récupérable",
        "ar": "الدولة — ضريبة القيمة المضافة القابلة للاسترداد",
        "type": AccountType.ASSET,
        "parent_code": "34",
    },
    # ---- Classe 4 : Passif circulant ----
    {
        "code": "4",
        "fr": "Comptes de passif circulant",
        "ar": "حسابات الخصوم المتداولة",
        "type": AccountType.LIABILITY,
        "parent_code": None,
    },
    {
        "code": "40",
        "fr": "Dettes du passif circulant",
        "ar": "ديون الخصوم المتداولة",
        "type": AccountType.LIABILITY,
        "parent_code": "4",
    },
    {
        "code": "401",
        "fr": "Fournisseurs et comptes rattachés",
        "ar": "الموردون والحسابات المرتبطة",
        "type": AccountType.LIABILITY,
        "parent_code": "40",
    },
    {
        "code": "44",
        "fr": "État — TVA facturée",
        "ar": "الدولة — ضريبة القيمة المضافة المحصلة",
        "type": AccountType.LIABILITY,
        "parent_code": "4",
    },
    {
        "code": "45",
        "fr": "Organismes sociaux",
        "ar": "الهيئات الاجتماعية",
        "type": AccountType.LIABILITY,
        "parent_code": "4",
    },
    {
        "code": "47",
        "fr": "Comptes transitoires ou d'attente",
        "ar": "الحسابات العابرة أو الانتظارية",
        "type": AccountType.LIABILITY,
        "parent_code": "4",
    },
    # ---- Classe 5 : Trésorerie ----
    {
        "code": "5",
        "fr": "Comptes de trésorerie",
        "ar": "حسابات الخزينة",
        "type": AccountType.TREASURY,
        "parent_code": None,
    },
    {
        "code": "51",
        "fr": "Trésorerie — Actif",
        "ar": "الخزينة — الأصول",
        "type": AccountType.TREASURY,
        "parent_code": "5",
    },
    {
        "code": "514",
        "fr": "Banques",
        "ar": "البنوك",
        "type": AccountType.TREASURY,
        "parent_code": "51",
    },
    {
        "code": "5141",
        "fr": "Banque principale",
        "ar": "البنك الرئيسي",
        "type": AccountType.TREASURY,
        "parent_code": "514",
    },
    {
        "code": "516",
        "fr": "Caisse",
        "ar": "الصندوق",
        "type": AccountType.TREASURY,
        "parent_code": "51",
    },
    {
        "code": "5161",
        "fr": "Caisse principale",
        "ar": "الصندوق الرئيسي",
        "type": AccountType.TREASURY,
        "parent_code": "516",
    },
    # ---- Classe 6 : Charges ----
    {
        "code": "6",
        "fr": "Comptes de charges",
        "ar": "حسابات الأعباء",
        "type": AccountType.EXPENSE,
        "parent_code": None,
    },
    {
        "code": "60",
        "fr": "Charges d'exploitation",
        "ar": "أعباء الاستغلال",
        "type": AccountType.EXPENSE,
        "parent_code": "6",
    },
    {
        "code": "601",
        "fr": "Achats de marchandises",
        "ar": "مشتريات البضائع",
        "type": AccountType.EXPENSE,
        "parent_code": "60",
    },
    {
        "code": "61",
        "fr": "Charges externes",
        "ar": "الأعباء الخارجية",
        "type": AccountType.EXPENSE,
        "parent_code": "6",
    },
    {
        "code": "62",
        "fr": "Impôts et taxes",
        "ar": "الضرائب والرسوم",
        "type": AccountType.EXPENSE,
        "parent_code": "6",
    },
    {
        "code": "63",
        "fr": "Charges de personnel",
        "ar": "أعباء الموظفين",
        "type": AccountType.EXPENSE,
        "parent_code": "6",
    },
    {
        "code": "64",
        "fr": "Autres charges d'exploitation",
        "ar": "أعباء الاستغلال الأخرى",
        "type": AccountType.EXPENSE,
        "parent_code": "6",
    },
    {
        "code": "65",
        "fr": "Dotations aux amortissements",
        "ar": "مخصصات الإهلاك",
        "type": AccountType.EXPENSE,
        "parent_code": "6",
    },
    {
        "code": "67",
        "fr": "Charges financières",
        "ar": "الأعباء المالية",
        "type": AccountType.EXPENSE,
        "parent_code": "6",
    },
    # ---- Classe 7 : Produits ----
    {
        "code": "7",
        "fr": "Comptes de produits",
        "ar": "حسابات المنتجات",
        "type": AccountType.REVENUE,
        "parent_code": None,
    },
    {
        "code": "70",
        "fr": "Produits d'exploitation",
        "ar": "منتجات الاستغلال",
        "type": AccountType.REVENUE,
        "parent_code": "7",
    },
    {
        "code": "701",
        "fr": "Ventes de marchandises",
        "ar": "مبيعات البضائع",
        "type": AccountType.REVENUE,
        "parent_code": "70",
    },
    {
        "code": "71",
        "fr": "Variations de stocks",
        "ar": "تغيرات المخزون",
        "type": AccountType.REVENUE,
        "parent_code": "7",
    },
    {
        "code": "73",
        "fr": "Produits accessoires",
        "ar": "المنتجات الإضافية",
        "type": AccountType.REVENUE,
        "parent_code": "7",
    },
    {
        "code": "74",
        "fr": "Subventions d'exploitation",
        "ar": "دعم الاستغلال",
        "type": AccountType.REVENUE,
        "parent_code": "7",
    },
    {
        "code": "75",
        "fr": "Autres produits d'exploitation",
        "ar": "منتجات الاستغلال الأخرى",
        "type": AccountType.REVENUE,
        "parent_code": "7",
    },
    {
        "code": "76",
        "fr": "Produits financiers",
        "ar": "المنتجات المالية",
        "type": AccountType.REVENUE,
        "parent_code": "7",
    },
    {
        "code": "77",
        "fr": "Produits non courants",
        "ar": "المنتجات غير الجارية",
        "type": AccountType.REVENUE,
        "parent_code": "7",
    },
]

DEFAULT_JOURNALS: list[dict] = [
    {"code": "JV", "fr": "Journal des ventes", "ar": "دفتر المبيعات", "type": JournalType.SALES},
    {
        "code": "JA",
        "fr": "Journal des achats",
        "ar": "دفتر المشتريات",
        "type": JournalType.PURCHASES,
    },
    {"code": "CAI", "fr": "Journal de caisse", "ar": "دفتر الصندوق", "type": JournalType.CASH},
    {"code": "BQ", "fr": "Journal de banque", "ar": "دفتر البنك", "type": JournalType.BANK},
    {"code": "OD", "fr": "Opérations diverses", "ar": "عمليات متنوعة", "type": JournalType.GENERAL},
]


class Command(BaseCommand):
    help = "Charge le Plan Comptable Marocain (PCM) et les journaux de base pour une coopérative."

    def add_arguments(self, parser):  # noqa: ANN001
        parser.add_argument(
            "--cooperative-id",
            type=str,
            required=True,
            help="UUID de la coopérative cible.",
        )

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        coop_id = options["cooperative_id"]
        try:
            cooperative = Cooperative.objects.get(pk=uuid.UUID(coop_id))
        except (Cooperative.DoesNotExist, ValueError) as exc:
            raise CommandError(f"Coopérative introuvable : {exc}") from exc

        self.stdout.write(f"Chargement du PCM pour : {cooperative.name}")

        # Charger les comptes en respectant la hiérarchie
        code_to_account: dict[str, Account] = {}
        created_count = 0
        skipped_count = 0

        for acc_data in PCM_ACCOUNTS:
            parent = (
                code_to_account.get(acc_data["parent_code"]) if acc_data["parent_code"] else None
            )
            account, created = Account.all_objects.get_or_create(
                cooperative=cooperative,
                code=acc_data["code"],
                defaults={
                    "name": {"fr": acc_data["fr"], "ar": acc_data["ar"]},
                    "account_type": acc_data["type"],
                    "parent": parent,
                    "is_system": True,
                    "is_active": True,
                },
            )
            code_to_account[acc_data["code"]] = account
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            f"  Comptes créés : {created_count}  |  Ignorés (déjà existants) : {skipped_count}"
        )

        # Charger les journaux
        j_created = 0
        for jdata in DEFAULT_JOURNALS:
            _, created = Journal.all_objects.get_or_create(
                cooperative=cooperative,
                code=jdata["code"],
                defaults={
                    "name": {"fr": jdata["fr"], "ar": jdata["ar"]},
                    "journal_type": jdata["type"],
                    "is_active": True,
                },
            )
            if created:
                j_created += 1

        self.stdout.write(f"  Journaux créés : {j_created}")
        self.stdout.write(self.style.SUCCESS("✓ PCM chargé avec succès."))
