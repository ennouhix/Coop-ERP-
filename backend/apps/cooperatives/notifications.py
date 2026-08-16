"""
Service centralisé d'envoi de notifications email.

Chaque fonction :
1. Crée un enregistrement EmailNotification (status=PENDING)
2. Tente d'envoyer l'email via send_cooperative_email()
3. Met à jour le statut (SENT / FAILED)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.utils import timezone

from apps.cooperatives.models import (
    EmailNotification,
    EmailNotificationStatus,
    EmailNotificationType,
)
from apps.cooperatives.services import send_cooperative_email

if TYPE_CHECKING:
    from apps.billing.models import Invoice, Payment
    from apps.contributions.models import Contribution
    from apps.cooperatives.models import Cooperative
    from apps.members.models import Member
    from apps.partners.models import Partner

logger = logging.getLogger(__name__)


def _create_and_send(
    *,
    cooperative: Cooperative,
    notification_type: str,
    recipient_email: str,
    recipient_name: str,
    subject: str,
    message: str,
    html_message: str | None = None,
    metadata: dict | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> EmailNotification:
    """Crée une notification et tente l'envoi."""
    notification = EmailNotification.objects.create(
        cooperative=cooperative,
        notification_type=notification_type,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        subject=subject,
        status=EmailNotificationStatus.PENDING,
        metadata=metadata or {},
    )

    try:
        send_cooperative_email(
            cooperative=cooperative,
            subject=subject,
            message=message,
            html_message=html_message,
            recipient_list=[recipient_email],
            attachments=attachments,
        )
        notification.status = EmailNotificationStatus.SENT
        notification.save(update_fields=["status"])
    except Exception as exc:
        logger.warning("Échec envoi email %s: %s", notification_type, exc)
        notification.status = EmailNotificationStatus.FAILED
        notification.error_message = str(exc)[:500]
        notification.save(update_fields=["status", "error_message"])

    return notification


# ======================================================================
# Facture émise → email au client
# ======================================================================

def notify_invoice_issued(invoice: Invoice) -> EmailNotification | None:
    """
    Envoie la facture émise au client par email avec le PDF en pièce jointe.

    Appelé depuis billing/services.py après issue_invoice().
    """
    partner: Partner = invoice.customer
    if not partner.email:
        logger.info(
            "Pas d'email pour le client %s, facture %s non envoyée.",
            partner.name,
            invoice.invoice_number,
        )
        return None

    coop: Cooperative = invoice.cooperative
    total = invoice.total_amount
    due = invoice.balance_due

    subject = f"Facture {invoice.invoice_number} — {coop.name}"
    message = (
        f"Bonjour {partner.name},\n\n"
        f"Veuillez trouver ci-joint la facture {invoice.invoice_number} "
        f"émise par {coop.name}.\n\n"
        f"Date d'émission : {invoice.issue_date}\n"
        f"Date d'échéance : {invoice.due_date}\n"
        f"Montant total : {total:,.2f} MAD\n"
        f"Montant dû : {due:,.2f} MAD\n\n"
        f"Merci de procéder au règlement avant la date d'échéance.\n\n"
        f"Cordialement,\n{coop.name}"
    )

    # --- Génération du PDF ---
    attachments = []
    try:
        from apps.reporting.pdf import generate_invoice_pdf
        pdf_buffer = generate_invoice_pdf(invoice)
        pdf_filename = f"Facture_{invoice.invoice_number}.pdf"
        attachments.append((pdf_filename, pdf_buffer.getvalue(), "application/pdf"))
    except Exception:
        logger.warning(
            "Erreur génération PDF facture %s", invoice.invoice_number, exc_info=True
        )

    return _create_and_send(
        cooperative=coop,
        notification_type=EmailNotificationType.INVOICE_ISSUED,
        recipient_email=partner.email,
        recipient_name=partner.name,
        subject=subject,
        message=message,
        attachments=attachments or None,
        metadata={
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "total_amount": str(total),
            "balance_due": str(due),
        },
    )


# ======================================================================
# Paiement reçu → confirmation au client
# ======================================================================

def notify_payment_received(
    payment: Payment, *, is_fully_paid: bool
) -> EmailNotification | None:
    """
    Envoie une confirmation de paiement au client.

    Appelé depuis billing/services.py après record_payment().
    """
    invoice: Invoice = payment.invoice
    partner: Partner = invoice.customer
    if not partner.email:
        return None

    coop: Cooperative = invoice.cooperative

    if is_fully_paid:
        status_text = "intégralement réglée"
    else:
        status_text = "partiellement réglée"

    subject = f"Paiement reçu — Facture {invoice.invoice_number} — {coop.name}"
    message = (
        f"Bonjour {partner.name},\n\n"
        f"Nous avons bien reçu votre paiement de {payment.amount:,.2f} MAD "
        f"pour la facture {invoice.invoice_number}.\n\n"
        f"La facture est maintenant {status_text}.\n"
        f"Solde restant dû : {invoice.balance_due:,.2f} MAD\n\n"
        f"Cordialement,\n{coop.name}"
    )

    return _create_and_send(
        cooperative=coop,
        notification_type=EmailNotificationType.PAYMENT_RECEIVED,
        recipient_email=partner.email,
        recipient_name=partner.name,
        subject=subject,
        message=message,
        metadata={
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "payment_amount": str(payment.amount),
            "payment_method": payment.payment_method,
            "balance_due": str(invoice.balance_due),
        },
    )


# ======================================================================
# Cotisation en attente → rappel au membre
# ======================================================================

def notify_contribution_pending(contribution: Contribution) -> EmailNotification | None:
    """
    Notifie un membre qu'une cotisation a été enregistrée à son nom.

    Appelé depuis contributions/services.py après create_contribution().
    """
    member: Member = contribution.member
    if not member.email:
        return None

    coop: Cooperative = contribution.cooperative

    subject = f"Cotisation enregistrée — {coop.name}"
    message = (
        f"Bonjour {member.first_name or member.last_name},\n\n"
        f"Une cotisation a été enregistrée à votre nom :\n\n"
        f"Campagne : {contribution.campaign}\n"
        f"Produit : {contribution.product}\n"
        f"Quantité : {contribution.quantity}\n"
        f"Montant : {contribution.total_amount:,.2f} MAD\n"
        f"Statut : En attente de paiement\n\n"
        f"Cordialement,\n{coop.name}"
    )

    return _create_and_send(
        cooperative=coop,
        notification_type=EmailNotificationType.CONTRIBUTION_PENDING,
        recipient_email=member.email,
        recipient_name=f"{member.first_name} {member.last_name}".strip(),
        subject=subject,
        message=message,
        metadata={
            "contribution_id": str(contribution.id),
            "campaign": contribution.campaign,
            "total_amount": str(contribution.total_amount),
        },
    )


# ======================================================================
# Relance facture en retard → email au client
# ======================================================================

def notify_overdue_invoice(invoice: Invoice) -> EmailNotification | None:
    """
    Envoie un rappel de paiement pour une facture en retard.

    Appelé depuis la management command send_overdue_reminders.
    """
    partner: Partner = invoice.customer
    if not partner.email:
        return None

    coop: Cooperative = invoice.cooperative
    days_overdue = (timezone.now().date() - invoice.due_date).days

    subject = (
        f"Rappel — Facture {invoice.invoice_number} en retard "
        f"({days_overdue} jours) — {coop.name}"
    )
    message = (
        f"Bonjour {partner.name},\n\n"
        f"Nous vous informons que la facture {invoice.invoice_number} "
        f"échelonnée au {invoice.due_date} présente un retard de "
        f"{days_overdue} jours.\n\n"
        f"Montant dû : {invoice.balance_due:,.2f} MAD\n\n"
        f"Merci de régulariser votre situation dans les meilleurs délais.\n\n"
        f"Cordialement,\n{coop.name}"
    )

    return _create_and_send(
        cooperative=coop,
        notification_type=EmailNotificationType.OVERDUE_REMINDER,
        recipient_email=partner.email,
        recipient_name=partner.name,
        subject=subject,
        message=message,
        metadata={
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "days_overdue": days_overdue,
            "balance_due": str(invoice.balance_due),
        },
    )
