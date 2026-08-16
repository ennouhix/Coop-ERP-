// Types du module Rôles & Permissions (panneau d'administration).

export type EditableUserRole = "admin" | "staff" | "accountant";

export const ROLE_PERMISSION_MODULES = [
  "users",
  "cooperative",
  "members",
  "partners",
  "catalog",
  "warehouses",
  "stock",
  "purchases",
  "sales",
  "billing",
  "reports",
  "audit",
  "accounting",
  "assemblies",
  "contributions",
] as const;

export const EDITABLE_ROLES: EditableUserRole[] = ["admin", "staff", "accountant"];

export interface RolePermissionsData {
  modules: string[];
  roles: Record<EditableUserRole, string[]>;
}
