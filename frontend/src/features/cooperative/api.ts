import { apiClient } from "../../api/client";
import type { Cooperative, CooperativeEmailConfig, CooperativeFormValues } from "./types";

export async function getCooperative(): Promise<Cooperative> {
  const { data } = await apiClient.get<Cooperative>("/cooperatives/me/");
  return data;
}

export async function updateCooperative(values: Partial<CooperativeFormValues>): Promise<Cooperative> {
  const { data } = await apiClient.patch<Cooperative>("/cooperatives/me/", values);
  return data;
}

export async function uploadCooperativeLogo(file: File): Promise<Cooperative> {
  const formData = new FormData();
  formData.append("logo", file);
  const { data } = await apiClient.post<Cooperative>("/cooperatives/me/logo/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteCooperativeLogo(): Promise<Cooperative> {
  const { data } = await apiClient.delete<Cooperative>("/cooperatives/me/logo/");
  return data;
}

export async function getEmailConfig(): Promise<CooperativeEmailConfig> {
  const { data } = await apiClient.get<CooperativeEmailConfig>("/cooperatives/me/email/");
  return data;
}

export async function updateEmailConfig(values: Partial<CooperativeEmailConfig>): Promise<CooperativeEmailConfig> {
  const { data } = await apiClient.patch<CooperativeEmailConfig>("/cooperatives/me/email/", values);
  return data;
}

export async function testEmailConnection(
  values: Partial<CooperativeEmailConfig>,
): Promise<{ success: boolean; message: string }> {
  const { data } = await apiClient.post<{ success: boolean; message: string }>(
    "/cooperatives/me/email/test/",
    values,
  );
  return data;
}

export interface EmailNotification {
  id: string;
  notification_type: string;
  notification_type_display: string;
  recipient_email: string;
  recipient_name: string;
  subject: string;
  status: string;
  status_display: string;
  error_message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export async function getNotifications(params?: {
  notification_type?: string;
  status?: string;
}): Promise<EmailNotification[]> {
  const { data } = await apiClient.get<EmailNotification[]>(
    "/cooperatives/me/notifications/",
    { params },
  );
  return data;
}
