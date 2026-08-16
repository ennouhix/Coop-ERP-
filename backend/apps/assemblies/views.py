"""
Vues du module assemblies.

Endpoints :
- GET    /api/v1/assemblies/                        -> liste (filtres)
- POST   /api/v1/assemblies/                        -> créer une assemblée
- GET    /api/v1/assemblies/{id}/                   -> détail
- PATCH  /api/v1/assemblies/{id}/                   -> modifier
- GET    /api/v1/assemblies/{assembly_id}/attendance/  -> liste des présences/votes
- POST   /api/v1/assemblies/{assembly_id}/attendance/  -> enregistrer une présence/vote
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.assemblies import services
from apps.assemblies.filters import AssemblyFilter
from apps.assemblies.models import Assembly, AssemblyAttendance
from apps.assemblies.serializers import (
    AssemblyAttendanceCreateSerializer,
    AssemblyAttendanceSerializer,
    AssemblyCreateSerializer,
    AssemblySerializer,
)
from apps.authentication.permissions import IsCooperativeMember
from apps.members.models import Member
from apps.roles_permissions.permissions import RequirePermission


class AssemblyListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AssemblyFilter
    ordering_fields = ["scheduled_date", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        return Assembly.all_objects.filter(cooperative_id=self.request.user.cooperative_id)

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "assemblies.edit" if self.request.method == "POST" else "assemblies.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return AssemblyCreateSerializer if self.request.method == "POST" else AssemblySerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = AssemblyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assembly = services.create_assembly(
            cooperative=request.user.cooperative, **serializer.validated_data
        )
        return Response(AssemblySerializer(assembly).data, status=status.HTTP_201_CREATED)


class AssemblyDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = AssemblySerializer

    def get_queryset(self):  # noqa: ANN201
        return Assembly.all_objects.filter(cooperative_id=self.request.user.cooperative_id)

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "assemblies.edit" if self.request.method in {"PATCH", "PUT"} else "assemblies.view"
        base.append(RequirePermission(code)())
        return base

    def perform_update(self, serializer) -> None:  # noqa: ANN001
        serializer.save(updated_by=self.request.user)


class AssemblyAttendanceListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):  # noqa: ANN201
        return AssemblyAttendance.all_objects.filter(
            cooperative_id=self.request.user.cooperative_id,
            assembly_id=self.kwargs["assembly_id"],
        ).select_related("member")

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "assemblies.edit" if self.request.method == "POST" else "assemblies.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return (
            AssemblyAttendanceCreateSerializer
            if self.request.method == "POST"
            else AssemblyAttendanceSerializer
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        assembly = get_object_or_404(
            Assembly.all_objects,
            pk=kwargs["assembly_id"],
            cooperative_id=request.user.cooperative_id,
        )
        serializer = AssemblyAttendanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        member = get_object_or_404(
            Member, pk=data["member_id"], cooperative_id=request.user.cooperative_id
        )
        attendance = services.register_attendance(
            cooperative=request.user.cooperative,
            assembly=assembly,
            member=member,
            attendance_status=data["attendance_status"],
            vote=data.get("vote"),
        )
        return Response(
            AssemblyAttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED
        )
