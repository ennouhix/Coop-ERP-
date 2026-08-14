import { apiClient } from "../../api/client";
import type { EditableUserRole, RolePermissionsData } from "./types";

export async function getRolePermissions(): Promise<RolePermissionsData> {
  const { data } = await apiClient.get<RolePermissionsData>("/roles/permissions/");
  return data;
}

export async function updateRolePermissions(
  roles: Record<EditableUserRole, string[]>,
): Promise<RolePermissionsData> {
  const { data } = await apiClient.put<RolePermissionsData>("/roles/permissions/", roles);
  return data;
}
