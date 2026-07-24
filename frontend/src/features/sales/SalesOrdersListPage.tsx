import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { OrderStatusBadge } from "../../shared/ui/OrderStatusBadge";
import { listSalesOrders } from "./api";
import type { SalesOrder, SalesOrderStatus } from "./types";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function SalesOrdersListPage() {
  const { t } = useTranslation();
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [status, setStatus] = useState<SalesOrderStatus | "">("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    listSalesOrders({ status })
      .then((data) => setOrders(data.results))
      .finally(() => setIsLoading(false));
  }, [status]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold text-ink-900">{t("sales.title")}</h1>
        <Link to="/sales/new">
          <Button><Plus className="h-4 w-4" />{t("sales.new")}</Button>
        </Link>
      </div>

      <div className="mt-6">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as SalesOrderStatus | "")}
          className="rounded-md border border-ink-900/15 px-3 py-2 text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
        >
          <option value="">{t("sales.status_all")}</option>
          <option value="draft">{t("sales.status_draft")}</option>
          <option value="confirmed">{t("sales.status_confirmed")}</option>
          <option value="partially_delivered">{t("sales.status_partially_delivered")}</option>
          <option value="delivered">{t("sales.status_delivered")}</option>
          <option value="cancelled">{t("sales.status_cancelled")}</option>
        </select>
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-ink-900/5 bg-white shadow-sm">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 text-xs font-medium uppercase tracking-wide text-ink-700/70">
            <tr>
              <th className="px-4 py-3 text-start">{t("sales.field.order_number")}</th>
              <th className="px-4 py-3 text-start">{t("sales.field.customer")}</th>
              <th className="px-4 py-3 text-start">{t("sales.field.order_date")}</th>
              <th className="px-4 py-3 text-start">{t("sales.field.total")}</th>
              <th className="px-4 py-3 text-start">{t("sales.field.status")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td></tr>
            )}
            {!isLoading && orders.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("sales.empty")}</td></tr>
            )}
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs text-ink-700">
                  <Link to={`/sales/${order.id}`} className="font-medium text-moss-700 hover:underline">
                    {order.order_number}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">{order.customer_name}</td>
                <td className="px-4 py-3 text-ink-700">{order.order_date}</td>
                <td className="px-4 py-3 font-medium text-ink-900">{formatMoney(order.total_amount)}</td>
                <td className="px-4 py-3"><OrderStatusBadge status={order.status} i18nPrefix="sales" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
