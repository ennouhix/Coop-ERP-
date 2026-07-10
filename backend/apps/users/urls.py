from __future__ import annotations

from django.urls import path

from apps.users.views import (
    AcceptInvitationView,
    ChangeUserRoleView,
    DeactivateUserView,
    InvitationCancelView,
    InvitationListCreateView,
    ReactivateUserView,
    TeamMemberListView,
)

app_name = "users"

urlpatterns = [
    path("", TeamMemberListView.as_view(), name="team-list"),
    path("<uuid:user_id>/role/", ChangeUserRoleView.as_view(), name="change-role"),
    path("<uuid:user_id>/deactivate/", DeactivateUserView.as_view(), name="deactivate"),
    path("<uuid:user_id>/reactivate/", ReactivateUserView.as_view(), name="reactivate"),
    path("invitations/", InvitationListCreateView.as_view(), name="invitation-list-create"),
    path("invitations/<uuid:invitation_id>/", InvitationCancelView.as_view(), name="invitation-cancel"),
    path("invitations/accept/", AcceptInvitationView.as_view(), name="invitation-accept"),
]
