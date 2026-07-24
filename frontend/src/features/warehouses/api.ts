import { apiClient } from "../../api/client";
import type { TeamMember, Warehouse, WarehouseFormValues } from "./types";

export async function listWarehouses(): Promise<Warehouse[]> {
  const { data } = await apiClient.get<{ results: Warehouse[] } | Warehouse[]>("/warehouses/");
  return Array.isArray(data) ? data : data.results;
}

export async function getWarehouse(id: string): Promise<Warehouse> {
  const { data } = await apiClient.get<Warehouse>(`/warehouses/${id}/`);
  return data;
}

export async function createWarehouse(values: WarehouseFormValues): Promise<Warehouse> {
  const { data } = await apiClient.post<Warehouse>("/warehouses/", values);
  return data;
}

export async function updateWarehouse(id: string, values: Partial<WarehouseFormValues>): Promise<Warehouse> {
  const { data } = await apiClient.patch<Warehouse>(`/warehouses/${id}/`, values);
  return data;
}

export async function setDefaultWarehouse(id: string): Promise<Warehouse> {
  const { data } = await apiClient.post<Warehouse>(`/warehouses/${id}/set-default/`);
  return data;
}

export async function deactivateWarehouse(id: string): Promise<void> {
  await apiClient.post(`/warehouses/${id}/deactivate/`);
}

export async function reactivateWarehouse(id: string): Promise<Warehouse> {
  const { data } = await apiClient.post<Warehouse>(`/warehouses/${id}/reactivate/`);
  return data;
}

export async function listTeamMembers(): Promise<TeamMember[]> {
  const { data } = await apiClient.get<{ results: TeamMember[] } | TeamMember[]>("/users/");
  return Array.isArray(data) ? data : data.results;
}
