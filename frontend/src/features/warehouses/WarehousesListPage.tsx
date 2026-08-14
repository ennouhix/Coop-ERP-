import { Plus, Star } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { listWarehouses, setDefaultWarehouse } from "./api";
import type { Warehouse } from "./types";

export function WarehousesListPage() {
  const { t } = useTranslation();
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    setIsLoading(true);
    listWarehouses()
      .then(setWarehouses)
      .finally(() => setIsLoading(false));
  }

  useEffect(refresh, []);

  async function handleSetDefault(id: string) {
    setError(null);
    try {
      await setDefaultWarehouse(id);
      refresh();
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">{t("warehouses.title")}</h1>
          <p className="page-heading-subtitle">{t("warehouses.count", { count: warehouses.length })}</p>
        </div>
        <Link to="/warehouses/new">
          <Button>
            <Plus className="h-4 w-4" />
            {t("warehouses.new")}
          </Button>
        </Link>
      </div>

      {error && <p role="alert" className="mt-4 text-start text-sm text-terracotta-600">{error}</p>}

      <div className="mt-6 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("warehouses.field.code")}</th>
              <th className="px-4 py-3 text-start">{t("warehouses.field.name")}</th>
              <th className="px-4 py-3 text-start">{t("warehouses.field.city")}</th>
              <th className="px-4 py-3 text-start">{t("warehouses.field.manager")}</th>
              <th className="px-4 py-3 text-start">{t("warehouses.field.status")}</th>
              <th className="px-4 py-3 text-start" />
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td></tr>
            )}
            {!isLoading && warehouses.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-ink-700">{t("warehouses.empty")}</td></tr>
            )}
            {warehouses.map((warehouse) => (
              <tr key={warehouse.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs text-ink-700">{warehouse.code}</td>
                <td className="px-4 py-3">
                  <Link to={`/warehouses/${warehouse.id}`} className="inline-flex items-center gap-1.5 font-medium text-moss-700 hover:underline">
                    {warehouse.is_default && <Star className="h-3.5 w-3.5 fill-ochre-500 text-ochre-500" />}
                    {warehouse.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">{warehouse.city || "—"}</td>
                <td className="px-4 py-3 text-ink-700">{warehouse.manager_name || "—"}</td>
                <td className="px-4 py-3">
                  <StatusBadge
                    label={warehouse.is_active ? t("warehouses.status_active") : t("warehouses.status_inactive")}
                    tone={warehouse.is_active ? "moss" : "neutral"}
                  />
                </td>
                <td className="px-4 py-3 text-end">
                  {!warehouse.is_default && warehouse.is_active && (
                    <button
                      onClick={() => handleSetDefault(warehouse.id)}
                      className="text-xs font-medium text-moss-700 hover:underline"
                    >
                      {t("warehouses.set_default")}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
