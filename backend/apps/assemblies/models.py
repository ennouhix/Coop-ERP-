"""
Modèles du module assemblies — les assemblées générales.

Le droit coopératif marocain (loi 112-12, ODCO) impose aux coopératives de
tenir régulièrement des assemblées générales : convocation, quorum, votes
des membres et procès-verbaux. Ce module suit la vie de ces assemblées et
la participation/vote de chaque adhérent.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantBaseModel


class AssemblyType(models.TextChoices):
    ORDINARY = "ordinary", "Assemblée générale ordinaire"
    EXTRAORDINARY = "extraordinary", "Assemblée générale extraordinaire"


class AssemblyStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    SCHEDULED = "scheduled", "Programmée"
    DONE = "done", "Tenue"
    CANCELLED = "cancelled", "Annulée"


class Assembly(TenantBaseModel):
    """Une assemblée générale de la coopérative."""

    title = models.CharField(max_length=255)
    assembly_type = models.CharField(
        max_length=20, choices=AssemblyType.choices, default=AssemblyType.ORDINARY
    )
    scheduled_date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    quorum_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("50.00"),
        help_text="Quorum requis pour la tenue de l'assemblée (en %).",
    )
    agenda = models.TextField(blank=True, help_text="Ordre du jour.")
    status = models.CharField(
        max_length=15, choices=AssemblyStatus.choices, default=AssemblyStatus.DRAFT
    )
    minutes_notes = models.TextField(blank=True, help_text="Procès-verbal / compte rendu.")

    class Meta:
        verbose_name = "Assemblée"
        verbose_name_plural = "Assemblées"
        ordering = ["-scheduled_date"]
        indexes = [
            models.Index(fields=["cooperative", "status"]),
        ]

    def __str__(self) -> str:
        return self.title


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Présent"
    ABSENT = "absent", "Absent"
    EXCUSED = "excused", "Excusé"


class VoteChoice(models.TextChoices):
    FOR = "for", "Pour"
    AGAINST = "against", "Contre"
    ABSTENTION = "abstention", "Abstention"


class AssemblyAttendance(TenantBaseModel):
    """Présence et vote d'un membre à une assemblée (une ligne par membre)."""

    assembly = models.ForeignKey(Assembly, on_delete=models.CASCADE, related_name="attendances")
    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="assembly_attendances"
    )
    attendance_status = models.CharField(
        max_length=10, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT
    )
    vote = models.CharField(  # noqa: DJ001 (null = membre présent sans vote enregistré)
        max_length=12, choices=VoteChoice.choices, null=True, blank=True, default=None
    )

    class Meta:
        verbose_name = "Présence à l'assemblée"
        verbose_name_plural = "Présences aux assemblées"
        constraints = [
            models.UniqueConstraint(
                fields=["assembly", "member"], name="unique_attendance_per_assembly_member"
            ),
        ]
        indexes = [
            models.Index(fields=["cooperative", "assembly"]),
        ]

    def __str__(self) -> str:
        return f"{self.member} @ {self.assembly}"
