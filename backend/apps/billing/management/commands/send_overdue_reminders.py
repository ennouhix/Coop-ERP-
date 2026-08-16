"""
Envoie des rappels de paiement pour les factures en retard.

Usage :
    python manage.py send_overdue_reminders

Peut être exécuté quotidiennement via cron :
    0 9 * * * cd /app && python manage.py send_overdue_reminders
"""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.billing.models import Invoice, InvoiceStatus
from apps.cooperatives.notifications import notify_overdue_invoice

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Envoie des rappels pour les factures en retard de paiement."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-days",
            type=int,
            default=3,
            help="Nombre minimum de jours de retard avant envoi (défaut: 3).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule l'envoi sans rien modifier.",
        )

    def handle(self, *args, **options):
        min_days = options["min_days"]
        dry_run = options["dry_run"]

        today = timezone.now().date()
        overdue_invoices = Invoice.objects.filter(
            status__in=[InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID],
            due_date__lt=today,
        ).select_related("customer", "cooperative")

        count = 0
        skipped = 0

        for invoice in overdue_invoices:
            days_overdue = (today - invoice.due_date).days
            if days_overdue < min_days:
                skipped += 1
                continue

            partner = invoice.customer
            if not partner.email:
                continue

            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] Rappel → {partner.email} | "
                    f"Facture {invoice.invoice_number} | "
                    f"{days_overdue} jours de retard | "
                    f"{invoice.balance_due:,.2f} MAD"
                )
                count += 1
                continue

            notify_overdue_invoice(invoice)
            count += 1
            self.stdout.write(
                f"Rappel envoyé → {partner.email} | "
                f"Facture {invoice.invoice_number} | "
                f"{days_overdue} jours | "
                f"{invoice.balance_due:,.2f} MAD"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTerminé : {count} rappel(s) envoyé(s), "
                f"{skipped} facture(s) ignorée(s) (< {min_days} jours)."
            )
        )
