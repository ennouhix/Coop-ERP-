"""
Logique métier du module assemblies.

`register_attendance` est un upsert : un membre ne peut avoir qu'une seule
ligne de présence par assemblée (contrainte unique assembly + member).
"""

from __future__ import annotations

from django.db import transaction

from apps.assemblies.models import Assembly, AssemblyAttendance, AttendanceStatus
from apps.cooperatives.models import Cooperative
from apps.members.models import Member


@transaction.atomic
def create_assembly(*, cooperative: Cooperative, **fields) -> Assembly:
    return Assembly.objects.create(cooperative=cooperative, **fields)


@transaction.atomic
def register_attendance(
    *,
    cooperative: Cooperative,
    assembly: Assembly,
    member: Member,
    attendance_status: str = AttendanceStatus.PRESENT,
    vote: str | None = None,
) -> AssemblyAttendance:
    """Crée ou met à jour la présence/vote d'un membre pour une assemblée."""
    attendance, _ = AssemblyAttendance.all_objects.update_or_create(
        assembly=assembly,
        member=member,
        defaults={
            "cooperative": cooperative,
            "attendance_status": attendance_status,
            "vote": vote,
        },
    )
    return attendance
