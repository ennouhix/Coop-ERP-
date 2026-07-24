import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { OrderStatusBadge } from "../../shared/ui/OrderStatusBadge";
import { listPurchaseOrders } from "./api";
import type { PurchaseOrder, PurchaseOrderStatus } from "./types";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function PurchaseOrdersListPage() {
  const { t } = useTranslation();
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [status, setStatus] = useState<PurchaseOrderStatus | "">("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    listPurchaseOrders({ status })
      .then((data) => setOrders(data.results))
      .finally(() => setIsLoading(false));
  }, [status]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold text-ink-900">{t("purchases.title")}</h1>
        <Link to="/purchases/new">
          <Button><Plus className="h-4 w-4" />{t("purchases.new")}</Button>
        </Link>
      </div>

      <div className="mt-6">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as PurchaseOrderStatus | "")}
          className="rounded-md border border-ink-900/15 px-3 py-2 text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
        >
          <option value="">{t("purchases.status_all")}</option>
          <option value="draft">{t("purchases.status_draft")}</option>
          <option value="confirmed">{t("purchases.status_confirmed")}</option>
          <option value="partially_received">{t("purchases.status_partially_received")}</option>
          <option value="received">{t("purchases.status_received")}</option>
          <option value="cancelled">{t("purchases.status_cancelled")}</option>
        </select>
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-ink-900/5 bg-white shadow-sm">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 text-xs font-medium uppercase tracking-wide text-ink-700/70">
            <tr>
              <th className="px-4 py-3 text-start">{t("purchases.field.order_number")}</th>
              <th className="px-4 py-3 text-start">{t("purchases.field.supplier")}</th>
              <th className="px-4 py-3 text-start">{t("purchases.field.order_date")}</th>
              <th className="px-4 py-3 text-start">{t("purchases.field.total")}</th>
              <th className="px-4 py-3 text-start">{t("purchases.field.status")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td></tr>
            )}
            {!isLoading && orders.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("purchases.empty")}</td></tr>
            )}
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs text-ink-700">
                  <Link to={`/purchases/${order.id}`} className="font-medium text-moss-700 hover:underline">
                    {order.order_number}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">{order.supplier_name}</td>
                <td className="px-4 py-3 text-ink-700">{order.order_date}</td>
                <td className="px-4 py-3 font-medium text-ink-900">{formatMoney(order.total_amount)}</td>
                <td className="px-4 py-3"><OrderStatusBadge status={order.status} i18nPrefix="purchases" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
