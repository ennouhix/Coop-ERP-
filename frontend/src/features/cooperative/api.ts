import { apiClient } from "../../api/client";
import type { Cooperative, CooperativeFormValues } from "./types";

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
