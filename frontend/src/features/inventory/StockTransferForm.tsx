import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { listProducts } from "../catalog/api";
import type { Product } from "../catalog/types";
import { listWarehouses } from "../warehouses/api";
import type { Warehouse } from "../warehouses/types";
import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextareaField, TextField } from "../../shared/ui/FormField";
import { recordStockTransfer } from "./api";
import { EMPTY_TRANSFER_FORM, type StockTransferFormValues } from "./types";

export function StockTransferForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<StockTransferFormValues>(EMPTY_TRANSFER_FORM);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    listProducts({}).then((data) => setProducts(data.results));
    listWarehouses().then(setWarehouses);
  }, []);

  function update<K extends keyof StockTransferFormValues>(key: K, value: StockTransferFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (values.from_warehouse_id && values.from_warehouse_id === values.to_warehouse_id) {
      setError(t("inventory.error_same_warehouse"));
      return;
    }

    setIsSubmitting(true);
    try {
      await recordStockTransfer(values);
      navigate("/inventory");
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="page-title">{t("inventory.action_transfer")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 card card-pad">
        <SelectField
          id="product_id" label={t("inventory.field.product")} required
          value={values.product_id} onChange={(e) => update("product_id", e.target.value)}
        >
          <option value="">{t("catalog.select_placeholder")}</option>
          {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name_display}</option>)}
        </SelectField>

        <div className="grid grid-cols-2 gap-4">
          <SelectField
            id="from_warehouse_id" label={t("inventory.field.from_warehouse")} required
            value={values.from_warehouse_id} onChange={(e) => update("from_warehouse_id", e.target.value)}
          >
            <option value="">{t("catalog.select_placeholder")}</option>
            {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </SelectField>
          <SelectField
            id="to_warehouse_id" label={t("inventory.field.to_warehouse")} required
            value={values.to_warehouse_id} onChange={(e) => update("to_warehouse_id", e.target.value)}
          >
            <option value="">{t("catalog.select_placeholder")}</option>
            {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </SelectField>
        </div>

        <TextField
          id="quantity" type="number" min={0.001} step="0.001" required
          label={t("inventory.field.quantity")}
          value={values.quantity} onChange={(e) => update("quantity", e.target.value)}
        />

        <TextField
          id="reference" label={t("inventory.field.reference")}
          value={values.reference} onChange={(e) => update("reference", e.target.value)}
        />

        <TextareaField
          id="notes" label={t("inventory.field.notes")}
          value={values.notes} onChange={(e) => update("notes", e.target.value)}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/inventory")}>
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
