import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { TranslatedTextField } from "../../shared/ui/TranslatedTextField";
import { createProduct, listCategories, listUnits } from "./api";
import { EMPTY_PRODUCT_FORM, type Category, type ProductFormValues, type Unit } from "./types";

export function ProductCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<ProductFormValues>(EMPTY_PRODUCT_FORM);
  const [units, setUnits] = useState<Unit[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    listUnits().then(setUnits);
    listCategories().then(setCategories);
  }, []);

  function update<K extends keyof ProductFormValues>(key: K, value: ProductFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (!values.unit) {
      setError(t("catalog.error_unit_required"));
      return;
    }

    setIsSubmitting(true);
    try {
      const product = await createProduct(values);
      navigate(`/catalog/${product.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (units.length === 0) {
    return (
      <div className="mx-auto max-w-2xl rounded-lg border border-ochre-400/30 bg-ochre-50 p-6 text-sm text-ink-800">
        {t("catalog.no_units_warning")}{" "}
        <a href="/catalog/reference-data" className="font-medium text-moss-700 hover:underline">
          {t("catalog.tab_reference_data")}
        </a>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="page-title">{t("catalog.new_product")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 card card-pad">
        <TranslatedTextField
          label={t("catalog.field.name")} required
          value={values.name} onChange={(v) => update("name", v)}
        />

        <div className="grid grid-cols-2 gap-4">
          <SelectField
            id="unit" label={t("catalog.field.unit")} required
            value={values.unit} onChange={(e) => update("unit", e.target.value)}
          >
            <option value="">{t("catalog.select_placeholder")}</option>
            {units.map((unit) => (
              <option key={unit.id} value={unit.id}>{unit.name} ({unit.symbol})</option>
            ))}
          </SelectField>
          <SelectField
            id="category" label={t("catalog.field.category")}
            value={values.category ?? ""} onChange={(e) => update("category", e.target.value || null)}
          >
            <option value="">{t("catalog.no_category")}</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name_display}</option>
            ))}
          </SelectField>
        </div>

        <TextField
          id="barcode" label={t("catalog.field.barcode")}
          value={values.barcode} onChange={(e) => update("barcode", e.target.value)}
        />

        <div className="grid grid-cols-3 gap-4">
          <TextField
            id="reference_purchase_price" type="number" min={0} step="0.01"
            label={t("catalog.field.purchase_price")}
            value={values.reference_purchase_price} onChange={(e) => update("reference_purchase_price", e.target.value)}
          />
          <TextField
            id="reference_sale_price" type="number" min={0} step="0.01"
            label={t("catalog.field.sale_price")}
            value={values.reference_sale_price} onChange={(e) => update("reference_sale_price", e.target.value)}
          />
          <TextField
            id="minimum_stock_threshold" type="number" min={0} step="0.001"
            label={t("catalog.field.min_stock")}
            value={values.minimum_stock_threshold} onChange={(e) => update("minimum_stock_threshold", e.target.value)}
          />
        </div>

        <TranslatedTextField
          label={t("catalog.field.description")} multiline
          value={values.description} onChange={(v) => update("description", v)}
        />

        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm text-ink-800">
            <input
              type="checkbox" checked={values.is_sellable}
              onChange={(e) => update("is_sellable", e.target.checked)}
              className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
            />
            {t("catalog.field.is_sellable")}
          </label>
          <label className="flex items-center gap-2 text-sm text-ink-800">
            <input
              type="checkbox" checked={values.is_purchasable}
              onChange={(e) => update("is_purchasable", e.target.checked)}
              className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
            />
            {t("catalog.field.is_purchasable")}
          </label>
        </div>

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/catalog")}>
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
