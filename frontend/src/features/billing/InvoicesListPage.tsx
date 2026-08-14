import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { OrderStatusBadge } from "../../shared/ui/OrderStatusBadge";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { listInvoices } from "./api";
import type { Invoice, InvoiceStatus } from "./types";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function InvoicesListPage() {
  const { t } = useTranslation();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [status, setStatus] = useState<InvoiceStatus | "">("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    listInvoices({ status })
      .then((data) => setInvoices(data.results))
      .finally(() => setIsLoading(false));
  }, [status]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="page-title">{t("billing.title")}</h1>
        <Link to="/billing/new">
          <Button><Plus className="h-4 w-4" />{t("billing.new")}</Button>
        </Link>
      </div>

      <div className="mt-6">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as InvoiceStatus | "")}
          className="input-inline"
        >
          <option value="">{t("billing.status_all")}</option>
          <option value="draft">{t("billing.status_draft")}</option>
          <option value="issued">{t("billing.status_issued")}</option>
          <option value="partially_paid">{t("billing.status_partially_paid")}</option>
          <option value="paid">{t("billing.status_paid")}</option>
          <option value="cancelled">{t("billing.status_cancelled")}</option>
        </select>
      </div>

      <div className="mt-4 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("billing.field.invoice_number")}</th>
              <th className="px-4 py-3 text-start">{t("billing.field.customer")}</th>
              <th className="px-4 py-3 text-start">{t("billing.field.due_date")}</th>
              <th className="px-4 py-3 text-start">{t("billing.field.balance_due")}</th>
              <th className="px-4 py-3 text-start">{t("billing.field.status")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td></tr>
            )}
            {!isLoading && invoices.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("billing.empty")}</td></tr>
            )}
            {invoices.map((invoice) => (
              <tr key={invoice.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs text-ink-700">
                  <Link to={`/billing/${invoice.id}`} className="font-medium text-moss-700 hover:underline">
                    {invoice.invoice_number}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">{invoice.customer_name}</td>
                <td className="px-4 py-3 text-ink-700">{invoice.due_date}</td>
                <td className="px-4 py-3 font-medium text-ink-900">{formatMoney(invoice.balance_due)}</td>
                <td className="px-4 py-3">
                  {invoice.is_overdue ? (
                    <StatusBadge label={t("billing.overdue")} tone="terracotta" />
                  ) : (
                    <OrderStatusBadge status={invoice.status} i18nPrefix="billing" />
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
