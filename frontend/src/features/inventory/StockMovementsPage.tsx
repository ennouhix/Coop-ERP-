import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { listWarehouses } from "../warehouses/api";
import type { Warehouse } from "../warehouses/types";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { InventoryTabs } from "./InventoryTabs";
import { listMovements } from "./api";
import type { MovementType, StockMovement } from "./types";

const TYPE_TONE: Record<MovementType, "moss" | "terracotta" | "ochre"> = {
  in: "moss",
  out: "terracotta",
  transfer: "ochre",
};

export function StockMovementsPage() {
  const { t } = useTranslation();
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState<MovementType | "">("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    listWarehouses().then(setWarehouses);
  }, []);

  useEffect(() => {
    setIsLoading(true);
    listMovements({ warehouse: warehouseFilter, movement_type: typeFilter })
      .then((data) => setMovements(data.results))
      .finally(() => setIsLoading(false));
  }, [warehouseFilter, typeFilter]);

  return (
    <div>
      <InventoryTabs />

      <h1 className="page-title">{t("inventory.tab_movements")}</h1>

      <div className="mt-6 flex gap-3">
        <select
          value={warehouseFilter}
          onChange={(e) => setWarehouseFilter(e.target.value)}
          className="input-inline"
        >
          <option value="">{t("inventory.all_warehouses")}</option>
          {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as MovementType | "")}
          className="input-inline"
        >
          <option value="">{t("inventory.all_types")}</option>
          <option value="in">{t("inventory.type_in")}</option>
          <option value="out">{t("inventory.type_out")}</option>
          <option value="transfer">{t("inventory.type_transfer")}</option>
        </select>
      </div>

      <div className="mt-4 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("inventory.field.date")}</th>
              <th className="px-4 py-3 text-start">{t("inventory.field.type")}</th>
              <th className="px-4 py-3 text-start">{t("inventory.field.product")}</th>
              <th className="px-4 py-3 text-start">{t("inventory.field.warehouse")}</th>
              <th className="px-4 py-3 text-start">{t("inventory.field.quantity")}</th>
              <th className="px-4 py-3 text-start">{t("inventory.field.reference")}</th>
              <th className="px-4 py-3 text-start">{t("inventory.field.author")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td></tr>
            )}
            {!isLoading && movements.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-ink-700">{t("inventory.empty_movements")}</td></tr>
            )}
            {movements.map((m) => (
              <tr key={m.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 text-xs text-ink-700">{new Date(m.created_at).toLocaleString("fr-MA")}</td>
                <td className="px-4 py-3">
                  <StatusBadge label={t(`inventory.type_${m.movement_type}`)} tone={TYPE_TONE[m.movement_type]} />
                </td>
                <td className="px-4 py-3 font-mono text-xs text-ink-700">{m.product_sku}</td>
                <td className="px-4 py-3 text-ink-700">
                  {m.warehouse_code}
                  {m.destination_warehouse_code && ` → ${m.destination_warehouse_code}`}
                </td>
                <td className="px-4 py-3 font-medium text-ink-900">{m.quantity}</td>
                <td className="px-4 py-3 text-ink-700">{m.reference || "—"}</td>
                <td className="px-4 py-3 text-ink-700">{m.created_by_name || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
