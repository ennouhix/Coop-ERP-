import { apiClient } from "../../api/client";

export interface PortalRegistrationValues {
  cooperative_name: string;
  owner_first_name: string;
  owner_last_name: string;
  owner_email: string;
  owner_password: string;
}

export interface PortalRegistrationResponse {
  message: string;
  cooperative_name: string;
  email: string;
}

export interface PortalActivationResponse {
  access: string;
  refresh: string;
  user: Record<string, unknown>;
  cooperative: Record<string, unknown>;
}

export async function registerPortalAccount(
  values: PortalRegistrationValues
): Promise<PortalRegistrationResponse> {
  const { data } = await apiClient.post<PortalRegistrationResponse>("/auth/register/", values);
  return data;
}

export async function activatePortalAccount(token: string): Promise<PortalActivationResponse> {
  const { data } = await apiClient.post<PortalActivationResponse>("/auth/register/verify/", {
    token,
  });
  return data;
}
