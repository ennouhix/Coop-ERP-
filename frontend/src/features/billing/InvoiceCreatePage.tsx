import { Plus, Trash2 } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { listProducts } from "../catalog/api";
import type { Product } from "../catalog/types";
import { listPartners } from "../partners/api";
import type { Partner } from "../partners/types";
import { listSalesOrders } from "../sales/api";
import type { SalesOrder } from "../sales/types";
import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextareaField, TextField } from "../../shared/ui/FormField";
import { createInvoiceFromOrder, createManualInvoice } from "./api";
import { EMPTY_MANUAL_INVOICE_FORM, EMPTY_MANUAL_LINE, type ManualInvoiceCreateValues } from "./types";

type Mode = "from_order" | "manual";

export function InvoiceCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("from_order");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // --- Mode "depuis une commande" ---
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [selectedOrderId, setSelectedOrderId] = useState("");
  const [issueDate, setIssueDate] = useState(new Date().toISOString().slice(0, 10));

  // --- Mode manuel ---
  const [manualValues, setManualValues] = useState<ManualInvoiceCreateValues>(EMPTY_MANUAL_INVOICE_FORM);
  const [customers, setCustomers] = useState<Partner[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    listSalesOrders({ status: "delivered" }).then((data) => {
      // On propose aussi les commandes partiellement livrées, en plus des livrées.
      listSalesOrders({ status: "partially_delivered" }).then((partial) => {
        setOrders([...data.results, ...partial.results]);
      });
    });
    listPartners({ is_customer: true }).then((data) => setCustomers(data.results));
    listProducts({}).then((data) => setProducts(data.results));
  }, []);

  function updateManualLine(index: number, field: keyof typeof EMPTY_MANUAL_LINE, value: string) {
    setManualValues((prev) => ({
      ...prev,
      lines: prev.lines.map((line, i) => (i === index ? { ...line, [field]: value } : line)),
    }));
  }

  function addManualLine() {
    setManualValues((prev) => ({ ...prev, lines: [...prev.lines, { ...EMPTY_MANUAL_LINE }] }));
  }

  function removeManualLine(index: number) {
    setManualValues((prev) => ({ ...prev, lines: prev.lines.filter((_, i) => i !== index) }));
  }

  async function handleSubmitFromOrder(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!selectedOrderId) {
      setError(t("billing.error_order_required"));
      return;
    }
    setIsSubmitting(true);
    try {
      const invoice = await createInvoiceFromOrder(selectedOrderId, issueDate);
      navigate(`/billing/${invoice.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSubmitManual(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (manualValues.lines.some((l) => !l.product_id || !l.quantity)) {
      setError(t("billing.error_lines_required"));
      return;
    }
    setIsSubmitting(true);
    try {
      const invoice = await createManualInvoice(manualValues);
      navigate(`/billing/${invoice.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="page-title">{t("billing.new")}</h1>

      <div className="mt-4 flex gap-2">
        <button
          onClick={() => setMode("from_order")}
          className={`rounded-md px-3 py-1.5 text-sm font-medium ${mode === "from_order" ? "bg-moss-600 text-white" : "bg-sand-100 text-ink-700"}`}
        >
          {t("billing.mode_from_order")}
        </button>
        <button
          onClick={() => setMode("manual")}
          className={`rounded-md px-3 py-1.5 text-sm font-medium ${mode === "manual" ? "bg-moss-600 text-white" : "bg-sand-100 text-ink-700"}`}
        >
          {t("billing.mode_manual")}
        </button>
      </div>

      {mode === "from_order" ? (
        <form onSubmit={handleSubmitFromOrder} className="mt-6 space-y-4 card card-pad">
          <SelectField
            id="order_id" label={t("billing.field.sales_order")} required
            value={selectedOrderId} onChange={(e) => setSelectedOrderId(e.target.value)}
          >
            <option value="">{t("catalog.select_placeholder")}</option>
            {orders.map((o) => (
              <option key={o.id} value={o.id}>{o.order_number} — {o.customer_name}</option>
            ))}
          </SelectField>
          {orders.length === 0 && (
            <p className="text-sm text-ink-700">{t("billing.no_deliverable_orders")}</p>
          )}
          <TextField
            id="issue_date" type="date" label={t("billing.field.issue_date")} required
            value={issueDate} onChange={(e) => setIssueDate(e.target.value)}
          />

          {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => navigate("/billing")}>{t("common.cancel")}</Button>
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? t("common.loading") : t("common.save")}</Button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleSubmitManual} className="mt-6 space-y-4 card card-pad">
          <SelectField
            id="customer_id" label={t("billing.field.customer")} required
            value={manualValues.customer_id} onChange={(e) => setManualValues((p) => ({ ...p, customer_id: e.target.value }))}
          >
            <option value="">{t("catalog.select_placeholder")}</option>
            {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </SelectField>

          <div className="grid grid-cols-2 gap-4">
            <TextField
              id="issue_date_manual" type="date" label={t("billing.field.issue_date")} required
              value={manualValues.issue_date} onChange={(e) => setManualValues((p) => ({ ...p, issue_date: e.target.value }))}
            />
            <TextField
              id="due_date" type="date" label={t("billing.field.due_date")}
              value={manualValues.due_date} onChange={(e) => setManualValues((p) => ({ ...p, due_date: e.target.value }))}
            />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-ink-800">{t("billing.lines_title")}</span>
              <Button type="button" variant="secondary" onClick={addManualLine}>
                <Plus className="h-4 w-4" />{t("billing.add_line")}
              </Button>
            </div>
            <div className="space-y-2">
              {manualValues.lines.map((line, index) => (
                <div key={index} className="grid grid-cols-[1fr,90px,90px,32px] items-end gap-2 rounded-md border border-ink-900/10 p-3">
                  <SelectField
                    id={`manual_product_${index}`} label={t("billing.field.product")}
                    value={line.product_id} onChange={(e) => updateManualLine(index, "product_id", e.target.value)}
                  >
                    <option value="">{t("catalog.select_placeholder")}</option>
                    {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name_display}</option>)}
                  </SelectField>
                  <TextField
                    id={`manual_qty_${index}`} type="number" min={0.001} step="0.001" label={t("billing.field.quantity")}
                    value={line.quantity} onChange={(e) => updateManualLine(index, "quantity", e.target.value)}
                  />
                  <TextField
                    id={`manual_price_${index}`} type="number" min={0} step="0.01" label={t("billing.field.unit_price")}
                    value={line.unit_price} onChange={(e) => updateManualLine(index, "unit_price", e.target.value)}
                  />
                  <button
                    type="button" onClick={() => removeManualLine(index)}
                    disabled={manualValues.lines.length === 1}
                    className="mb-2 flex h-9 w-8 items-center justify-center rounded-md text-terracotta-600 hover:bg-terracotta-500/10 disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <TextareaField
            id="notes" label={t("billing.field.notes")}
            value={manualValues.notes} onChange={(e) => setManualValues((p) => ({ ...p, notes: e.target.value }))}
          />

          {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => navigate("/billing")}>{t("common.cancel")}</Button>
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? t("common.loading") : t("common.save")}</Button>
          </div>
        </form>
      )}
    </div>
  );
}
