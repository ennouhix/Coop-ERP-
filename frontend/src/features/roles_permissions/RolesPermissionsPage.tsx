import { RotateCcw, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../shared/ui/Button";
import { useAuthStore } from "../auth/authStore";
import { getRolePermissions, updateRolePermissions } from "./api";
import { EDITABLE_ROLES, ROLE_PERMISSION_MODULES, type EditableUserRole } from "./types";

export function RolesPermissionsPage() {
  const { t } = useTranslation();
  const currentUser = useAuthStore((state) => state.user);
  const canManage = currentUser?.role === "owner" || currentUser?.role === "admin";

  const [modules, setModules] = useState<string[]>([...ROLE_PERMISSION_MODULES]);
  const [draft, setDraft] = useState<Record<EditableUserRole, Set<string>> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!canManage) {
      setIsLoading(false);
      return;
    }
    getRolePermissions()
      .then((data) => {
        setModules(data.modules);
        setDraft({
          admin: new Set(data.roles.admin),
          staff: new Set(data.roles.staff),
          accountant: new Set(data.roles.accountant),
        });
      })
      .catch(() => setError(t("rolesPermissions.error_load")))
      .finally(() => setIsLoading(false));
  }, [canManage, t]);

  function toggle(role: EditableUserRole, module: string) {
    setDraft((prev) => {
      if (!prev) return prev;
      const next = new Set(prev[role]);
      if (next.has(module)) {
        next.delete(module);
      } else {
        next.add(module);
      }
      return { ...prev, [role]: next };
    });
    setSaved(false);
  }

  async function handleSave() {
    if (!draft) return;
    setIsSaving(true);
    setError("");
    try {
      const updated = await updateRolePermissions({
        admin: [...draft.admin],
        staff: [...draft.staff],
        accountant: [...draft.accountant],
      });
      setDraft({
        admin: new Set(updated.roles.admin),
        staff: new Set(updated.roles.staff),
        accountant: new Set(updated.roles.accountant),
      });
      setSaved(true);
    } catch {
      setError(t("rolesPermissions.error_save"));
    } finally {
      setIsSaving(false);
    }
  }

  function handleReset() {
    setError("");
    setSaved(false);
    setIsLoading(true);
    getRolePermissions()
      .then((data) => {
        setModules(data.modules);
        setDraft({
          admin: new Set(data.roles.admin),
          staff: new Set(data.roles.staff),
          accountant: new Set(data.roles.accountant),
        });
      })
      .catch(() => setError(t("rolesPermissions.error_load")))
      .finally(() => setIsLoading(false));
  }

  if (!canManage) {
    return <p className="text-ink-700">{t("rolesPermissions.access_denied")}</p>;
  }

  if (isLoading || !draft) {
    return <p className="text-ink-700">{t("common.loading")}</p>;
  }

  return (
    <div className="max-w-4xl">
      <h1 className="page-title">{t("rolesPermissions.title")}</h1>
      <p className="page-heading-subtitle">{t("rolesPermissions.subtitle")}</p>

      <div className="mt-6 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("rolesPermissions.field.module")}</th>
              {EDITABLE_ROLES.map((role) => (
                <th key={role} className="px-4 py-3 text-center">
                  {t(`roles.${role}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {modules.map((module) => (
              <tr key={module} className="hover:bg-sand-50">
                <td className="px-4 py-2.5 font-medium text-ink-900">
                  {t(`rolesPermissions.modules.${module}`)}
                </td>
                {EDITABLE_ROLES.map((role) => (
                  <td key={role} className="px-4 py-2.5 text-center">
                    <input
                      type="checkbox"
                      checked={draft[role].has(module)}
                      onChange={() => toggle(role, module)}
                      className="h-4 w-4 rounded border-ink-900/20 accent-moss-600 focus:ring-moss-500/30"
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {error && <p className="mt-3 text-start text-sm text-terracotta-600">{error}</p>}
      {saved && <p className="mt-3 text-start text-sm text-moss-700">{t("common.saved")}</p>}

      <div className="mt-4 flex items-center gap-2">
        <Button type="button" onClick={handleSave} disabled={isSaving}>
          <Save className="h-4 w-4" />
          {t("common.save")}
        </Button>
        <Button type="button" variant="secondary" onClick={handleReset} disabled={isSaving}>
          <RotateCcw className="h-4 w-4" />
          {t("rolesPermissions.reset")}
        </Button>
      </div>
    </div>
  );
}
