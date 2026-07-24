import { apiClient } from "../../api/client";
import type {
  AcceptInvitationValues,
  Invitation,
  InvitationListResponse,
  InviteFormValues,
  TeamMember,
  TeamMemberListResponse,
  UserRole,
} from "./types";

/**
 * Les listes équipe/invitations sont paginées par défaut côté API
 * (PageNumberPagination, page_size=20). Une coopérative dépasse rarement
 * 100 comptes utilisateurs : on demande le max_page_size en une seule
 * requête plutôt que de paginer l'UI, ce qui suffit largement en pratique.
 */
const LIST_ALL_PARAMS = { page_size: 100 };

export async function listTeamMembers(): Promise<TeamMember[]> {
  const { data } = await apiClient.get<TeamMemberListResponse>("/users/", { params: LIST_ALL_PARAMS });
  return data.results;
}

export async function changeUserRole(userId: string, role: UserRole): Promise<TeamMember> {
  const { data } = await apiClient.patch<TeamMember>(`/users/${userId}/role/`, { role });
  return data;
}

export async function deactivateUser(userId: string): Promise<void> {
  await apiClient.post(`/users/${userId}/deactivate/`);
}

export async function reactivateUser(userId: string): Promise<TeamMember> {
  const { data } = await apiClient.post<TeamMember>(`/users/${userId}/reactivate/`);
  return data;
}

export async function listInvitations(): Promise<Invitation[]> {
  const { data } = await apiClient.get<InvitationListResponse>("/users/invitations/", {
    params: LIST_ALL_PARAMS,
  });
  return data.results;
}

export async function createInvitation(values: InviteFormValues): Promise<Invitation> {
  const { data } = await apiClient.post<Invitation>("/users/invitations/", values);
  return data;
}

export async function cancelInvitation(invitationId: string): Promise<void> {
  await apiClient.delete(`/users/invitations/${invitationId}/`);
}

export async function acceptInvitation(
  values: AcceptInvitationValues
): Promise<{ access: string; refresh: string }> {
  const { data } = await apiClient.post("/users/invitations/accept/", values);
  return data;
}
