import { apiClient } from "../../api/client";
import type { Member, MemberFormValues, MemberListResponse, MemberStatus } from "./types";

/**
 * `birth_date` est un DateField optionnel côté Django (null=True). Une
 * chaîne vide "" n'est PAS une valeur de date valide pour DRF (contrairement
 * à un CharField avec blank=True) — l'envoyer tel quel déclenche une erreur
 * de validation 400 que l'écran affichait comme "Une erreur est survenue."
 * sans plus de détail. On omet le champ s'il est vide plutôt que d'envoyer "".
 */
function normalizeMemberPayload<T extends { birth_date?: string }>(values: T): Omit<T, "birth_date"> & { birth_date?: string } {
  const { birth_date, ...rest } = values;
  return birth_date ? { ...rest, birth_date } : rest;
}

export interface MemberListParams {
  search?: string;
  status?: MemberStatus | "";
  page?: number;
}

export async function listMembers(params: MemberListParams): Promise<MemberListResponse> {
  const { data } = await apiClient.get<MemberListResponse>("/members/", {
    params: {
      search: params.search || undefined,
      status: params.status || undefined,
      page: params.page,
    },
  });
  return data;
}

export async function getMember(id: string): Promise<Member> {
  const { data } = await apiClient.get<Member>(`/members/${id}/`);
  return data;
}

export async function createMember(values: MemberFormValues): Promise<Member> {
  const { data } = await apiClient.post<Member>("/members/", normalizeMemberPayload(values));
  return data;
}

export async function updateMember(id: string, values: Partial<MemberFormValues>): Promise<Member> {
  const { data } = await apiClient.patch<Member>(`/members/${id}/`, normalizeMemberPayload(values));
  return data;
}

export async function deactivateMember(id: string): Promise<void> {
  await apiClient.post(`/members/${id}/deactivate/`);
}

export async function reactivateMember(id: string): Promise<Member> {
  const { data } = await apiClient.post<Member>(`/members/${id}/reactivate/`);
  return data;
}
