"""
Services du module documents (M16) : génération et archivage des PDF.

Chaque document est archivé dans DocumentArchive pour permettre un
re-téléchargement identique (copie figée) même si la commande source
évolue ensuite (livraison partielle supplémentaire, etc.).
"""

from __future__ import annotations

from apps.audit.services import log_activity
from apps.documents import pdf
from apps.documents.models import (
    DocumentArchive,
    DocumentSourceType,
    DocumentTemplateType,
    is_valid_source_id,
)


class DocumentError(Exception):
    """Erreur métier générique (message destiné à être affiché tel quel)."""


def generate_document(order, doc_type: str, *, actor, regenerate: bool = False) -> DocumentArchive:  # noqa: ANN001
    """
    Génère (ou réutilise) le PDF archivé d'un document commercial.

    - Si une archive existe déjà pour (coopérative, type, commande) et que
      `regenerate` est faux, elle est renvoyée telle quelle.
    - Sinon le PDF est (re)généré puis l'archive écrasée (Upsert).
    """
    if not is_valid_source_id(order.pk):
        raise DocumentError("Identifiant de la commande source invalide.")

    source_type = (
        DocumentSourceType.SALES_ORDER
        if doc_type == DocumentTemplateType.DELIVERY_NOTE
        else DocumentSourceType.PURCHASE_ORDER
    )
    source_id = order.pk
    source_number = order.order_number

    existing = DocumentArchive.objects.filter(
        cooperative=order.cooperative,
        doc_type=doc_type,
        source_id=source_id,
    ).first()
    if existing and not regenerate:
        return existing

    if doc_type == DocumentTemplateType.DELIVERY_NOTE:
        buffer = pdf.generate_delivery_note_pdf(order)
    elif doc_type == DocumentTemplateType.PURCHASE_ORDER:
        buffer = pdf.generate_purchase_order_pdf(order)
    elif doc_type == DocumentTemplateType.RECEIPT:
        buffer = pdf.generate_receipt_pdf(order)
    else:
        raise DocumentError(f"Type de document inconnu : {doc_type}")

    filename = f"{doc_type}_{source_number}.pdf"

    if existing:
        existing.pdf_file.save(filename, buffer, save=False)
        existing.filename = filename
        existing.save(update_fields=["pdf_file", "filename", "updated_by"])
        archive = existing
    else:
        archive = DocumentArchive(
            cooperative=order.cooperative,
            doc_type=doc_type,
            source_type=source_type,
            source_id=source_id,
            source_number=source_number,
            filename=filename,
            created_by=actor,
        )
        archive.pdf_file.save(filename, buffer, save=False)
        archive.save()

    log_activity(
        cooperative=order.cooperative,
        actor=actor,
        action="document.generated" if not existing else "document.regenerated",
        target_type="DocumentArchive",
        target_id=archive.id,
        target_repr=f"{archive.get_doc_type_display()} {source_number}",
        metadata={
            "doc_type": doc_type,
            "source_number": source_number,
            "regenerate": bool(regenerate),
        },
    )
    return archive
