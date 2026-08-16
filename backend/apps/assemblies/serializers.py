"""Serializers du module assemblies."""

from __future__ import annotations

from rest_framework import serializers

from apps.assemblies.models import (
    Assembly,
    AssemblyAttendance,
    AttendanceStatus,
    VoteChoice,
)


class AssemblySerializer(serializers.ModelSerializer):
    attendances_count = serializers.SerializerMethodField()
    present_count = serializers.SerializerMethodField()

    class Meta:
        model = Assembly
        fields = [
            "id",
            "title",
            "assembly_type",
            "scheduled_date",
            "location",
            "quorum_percent",
            "agenda",
            "status",
            "minutes_notes",
            "attendances_count",
            "present_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_attendances_count(self, obj: Assembly) -> int:
        return obj.attendances.count()

    def get_present_count(self, obj: Assembly) -> int:
        return obj.attendances.filter(attendance_status=AttendanceStatus.PRESENT).count()


class AssemblyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assembly
        fields = [
            "title",
            "assembly_type",
            "scheduled_date",
            "location",
            "quorum_percent",
            "agenda",
            "status",
            "minutes_notes",
        ]


class AssemblyAttendanceSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    member_number = serializers.CharField(source="member.member_number", read_only=True)

    class Meta:
        model = AssemblyAttendance
        fields = [
            "id",
            "assembly",
            "member",
            "member_name",
            "member_number",
            "attendance_status",
            "vote",
            "created_at",
        ]
        read_only_fields = ["id", "assembly", "created_at"]


class AssemblyAttendanceCreateSerializer(serializers.Serializer):
    """
    Enregistrement d'une présence/vote. `member_id` est résolu dans la vue
    au sein de la coopérative de l'utilisateur (règle du module inventory :
    jamais de queryset évaluée à l'import dans le corps d'un serializer).
    """

    member_id = serializers.UUIDField()
    attendance_status = serializers.ChoiceField(
        choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT
    )
    vote = serializers.ChoiceField(choices=VoteChoice.choices, required=False, allow_null=True)
