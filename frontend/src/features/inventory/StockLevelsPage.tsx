import { AlertTriangle, ArrowLeftRight, PackageMinus, PackagePlus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { listWarehouses } from "../warehouses/api";
import type { Warehouse } from "../warehouses/types";
import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { InventoryTabs } from "./InventoryTabs";
import { listStockLevels } from "./api";
import type { StockLevel } from "./types";

export function StockLevelsPage() {
  const { t } = useTranslation();
  const [levels, setLevels] = useState<StockLevel[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    listWarehouses().then(setWarehouses);
  }, []);

  useEffect(() => {
    setIsLoading(true);
    listStockLevels({ warehouse: warehouseFilter })
      .then((data) => setLevels(data.results))
      .finally(() => setIsLoading(false));
  }, [warehouseFilter]);

  return (
    <div>
      <InventoryTabs />

      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold text-ink-900">{t("inventory.tab_levels")}</h1>
        <div className="flex gap-2">
          <Link to="/inventory/movements/in">
            <Button variant="secondary"><PackagePlus className="h-4 w-4" />{t("inventory.action_in")}</Button>
          </Link>
          <Link to="/inventory/movements/out">
            <Button variant="secondary"><PackageMinus className="h-4 w-4" />{t("inventory.action_out")}</Button>
          </Link>
          <Link to="/inventory/movements/transfer">
            <Button variant="secondary"><ArrowLeftRight className="h-4 w-4" />{t("inventory.action_transfer")}</Button>
          </Link>
        </div>
      </div>

      <div className="mt-6">
        <select
          value={warehouseFilter}
          onChange={(e) => setWarehouseFilter(e.target.value)}
          className="rounded-md border border-ink-900/15 px-3 py-2 text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
        >
          <option value="">{t("inventory.all_warehouses")}</option>
          {warehouses.map((w) => (
            <option key={w.id} value={w.id}>{w.name}</option>
          ))}
        </select>
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-ink-900/5 bg-white shadow-sm">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 text-xs font-medium uppercase tracking-wide text-ink-700/70">
            <tr>
              <th className="px-4 py-3 text-start">{t("inventory.field.product")}</th>
              <th className="px-4 py-3 text-start">{t("inventory.field.warehouse")}</th>
              <th className="px-4 py-3 text-start">{t("inventory.field.quantity")}</th>
              <th className="px-4 py-3 text-start" />
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td></tr>
            )}
            {!isLoading && levels.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-ink-700">{t("inventory.empty_levels")}</td></tr>
            )}
            {levels.map((level) => (
              <tr key={level.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs text-ink-700">{level.product_sku}</td>
                <td className="px-4 py-3 text-ink-700">{level.warehouse_code}</td>
                <td className="px-4 py-3 font-medium text-ink-900">
                  {level.quantity} <span className="text-xs font-normal text-ink-700/60">{level.unit_symbol}</span>
                </td>
                <td className="px-4 py-3">
                  {level.is_below_threshold && (
                    <StatusBadge label={t("inventory.low_stock")} tone="terracotta" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {levels.some((l) => l.is_below_threshold) && (
        <p className="mt-3 flex items-center gap-1.5 text-xs text-terracotta-600">
          <AlertTriangle className="h-3.5 w-3.5" />
          {t("inventory.low_stock_hint")}
        </p>
      )}
    </div>
  );
}
