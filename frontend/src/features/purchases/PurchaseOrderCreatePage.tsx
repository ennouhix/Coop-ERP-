import { Plus, Trash2 } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { listProducts } from "../catalog/api";
import type { Product } from "../catalog/types";
import { listPartners } from "../partners/api";
import type { Partner } from "../partners/types";
import { listWarehouses } from "../warehouses/api";
import type { Warehouse } from "../warehouses/types";
import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextareaField, TextField } from "../../shared/ui/FormField";
import { createPurchaseOrder } from "./api";
import { EMPTY_LINE, EMPTY_PURCHASE_ORDER_FORM, type PurchaseOrderCreateValues } from "./types";

function formatMoney(value: number): string {
  return `${value.toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function PurchaseOrderCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<PurchaseOrderCreateValues>(EMPTY_PURCHASE_ORDER_FORM);
  const [suppliers, setSuppliers] = useState<Partner[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    listPartners({ is_supplier: true }).then((data) => setSuppliers(data.results));
    listWarehouses().then(setWarehouses);
    listProducts({}).then((data) => setProducts(data.results));
  }, []);

  function updateLine(index: number, field: keyof typeof EMPTY_LINE, value: string) {
    setValues((prev) => ({
      ...prev,
      lines: prev.lines.map((line, i) => (i === index ? { ...line, [field]: value } : line)),
    }));
  }

  function addLine() {
    setValues((prev) => ({ ...prev, lines: [...prev.lines, { ...EMPTY_LINE }] }));
  }

  function removeLine(index: number) {
    setValues((prev) => ({ ...prev, lines: prev.lines.filter((_, i) => i !== index) }));
  }

  const total = values.lines.reduce(
    (sum, line) => sum + (Number(line.quantity_ordered) || 0) * (Number(line.unit_price) || 0), 0
  );

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (values.lines.length === 0 || values.lines.some((l) => !l.product_id || !l.quantity_ordered)) {
      setError(t("purchases.error_lines_required"));
      return;
    }

    setIsSubmitting(true);
    try {
      const order = await createPurchaseOrder(values);
      navigate(`/purchases/${order.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="page-title">{t("purchases.new")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5 card card-pad">
        <div className="grid grid-cols-2 gap-4">
          <SelectField
            id="supplier_id" label={t("purchases.field.supplier")} required
            value={values.supplier_id} onChange={(e) => setValues((p) => ({ ...p, supplier_id: e.target.value }))}
          >
            <option value="">{t("catalog.select_placeholder")}</option>
            {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </SelectField>
          <SelectField
            id="warehouse_id" label={t("purchases.field.warehouse")} required
            value={values.warehouse_id} onChange={(e) => setValues((p) => ({ ...p, warehouse_id: e.target.value }))}
          >
            <option value="">{t("catalog.select_placeholder")}</option>
            {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </SelectField>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="order_date" type="date" label={t("purchases.field.order_date")} required
            value={values.order_date} onChange={(e) => setValues((p) => ({ ...p, order_date: e.target.value }))}
          />
          <TextField
            id="expected_delivery_date" type="date" label={t("purchases.field.expected_delivery_date")}
            value={values.expected_delivery_date} onChange={(e) => setValues((p) => ({ ...p, expected_delivery_date: e.target.value }))}
          />
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-ink-800">{t("purchases.lines_title")}</span>
            <Button type="button" variant="secondary" onClick={addLine}>
              <Plus className="h-4 w-4" />{t("purchases.add_line")}
            </Button>
          </div>

          <div className="space-y-2">
            {values.lines.map((line, index) => (
              <div key={index} className="grid grid-cols-[1fr,110px,110px,32px] items-end gap-2 rounded-md border border-ink-900/10 p-3">
                <SelectField
                  id={`line_product_${index}`} label={t("purchases.field.product")}
                  value={line.product_id} onChange={(e) => updateLine(index, "product_id", e.target.value)}
                >
                  <option value="">{t("catalog.select_placeholder")}</option>
                  {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name_display}</option>)}
                </SelectField>
                <TextField
                  id={`line_qty_${index}`} type="number" min={0.001} step="0.001" label={t("purchases.field.quantity")}
                  value={line.quantity_ordered} onChange={(e) => updateLine(index, "quantity_ordered", e.target.value)}
                />
                <TextField
                  id={`line_price_${index}`} type="number" min={0} step="0.01" label={t("purchases.field.unit_price")}
                  value={line.unit_price} onChange={(e) => updateLine(index, "unit_price", e.target.value)}
                />
                <button
                  type="button" onClick={() => removeLine(index)}
                  disabled={values.lines.length === 1}
                  className="mb-2 flex h-9 w-8 items-center justify-center rounded-md text-terracotta-600 hover:bg-terracotta-500/10 disabled:cursor-not-allowed disabled:opacity-30"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <p className="mt-3 text-end text-sm font-semibold text-ink-900">
            {t("purchases.total")} : {formatMoney(total)}
          </p>
        </div>

        <TextareaField
          id="notes" label={t("purchases.field.notes")}
          value={values.notes} onChange={(e) => setValues((p) => ({ ...p, notes: e.target.value }))}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/purchases")}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t("common.loading") : t("common.save")}
          </Button>
        </div>
      </form>
    </div>
  );
}
