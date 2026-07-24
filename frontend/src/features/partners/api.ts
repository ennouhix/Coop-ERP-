import { apiClient } from "../../api/client";
import type { Partner, PartnerFormValues, PartnerListResponse, PartnerStatus } from "./types";

export interface PartnerListParams {
  search?: string;
  status?: PartnerStatus | "";
  is_customer?: boolean;
  is_supplier?: boolean;
  page?: number;
}

export async function listPartners(params: PartnerListParams): Promise<PartnerListResponse> {
  const { data } = await apiClient.get<PartnerListResponse>("/partners/", {
    params: {
      search: params.search || undefined,
      status: params.status || undefined,
      is_customer: params.is_customer || undefined,
      is_supplier: params.is_supplier || undefined,
      page: params.page,
    },
  });
  return data;
}

export async function getPartner(id: string): Promise<Partner> {
  const { data } = await apiClient.get<Partner>(`/partners/${id}/`);
  return data;
}

export async function createPartner(values: PartnerFormValues): Promise<Partner> {
  const { data } = await apiClient.post<Partner>("/partners/", values);
  return data;
}

export async function updatePartner(id: string, values: Partial<PartnerFormValues>): Promise<Partner> {
  const { data } = await apiClient.patch<Partner>(`/partners/${id}/`, values);
  return data;
}

export async function deactivatePartner(id: string): Promise<void> {
  await apiClient.post(`/partners/${id}/deactivate/`);
}

export async function reactivatePartner(id: string): Promise<Partner> {
  const { data } = await apiClient.post<Partner>(`/partners/${id}/reactivate/`);
  return data;
}
