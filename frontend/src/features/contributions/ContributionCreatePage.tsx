import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextareaField, TextField } from "../../shared/ui/FormField";
import { listProducts } from "../catalog/api";
import type { Product } from "../catalog/types";
import { listMembers } from "../members/api";
import type { Member } from "../members/types";
import { createContribution } from "./api";
import { EMPTY_CONTRIBUTION_FORM, type ContributionFormValues } from "./types";

export function ContributionCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<ContributionFormValues>(EMPTY_CONTRIBUTION_FORM);
  const [members, setMembers] = useState<Member[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([listMembers({}), listProducts({})])
      .then(([membersData, productsData]) => {
        setMembers(membersData.results);
        setProducts(productsData.results);
      })
      .finally(() => setIsLoadingOptions(false));
  }, []);

  function update<K extends keyof ContributionFormValues>(key: K, value: ContributionFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const contribution = await createContribution(values);
      navigate(`/contributions/${contribution.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="page-title">{t("contributions.new")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 card card-pad">
        <div className="grid grid-cols-2 gap-4">
          <SelectField
            id="member_id" label={t("contributions.field.member")} required
            value={values.member_id}
            onChange={(e) => update("member_id", e.target.value)}
          >
            <option value="">{isLoadingOptions ? t("common.loading") : t("contributions.select_member")}</option>
            {members.map((member) => (
              <option key={member.id} value={member.id}>
                {member.member_number} — {member.full_name}
              </option>
            ))}
          </SelectField>

          <SelectField
            id="product_id" label={t("contributions.field.product")} required
            value={values.product_id}
            onChange={(e) => update("product_id", e.target.value)}
          >
            <option value="">{isLoadingOptions ? t("common.loading") : t("contributions.select_product")}</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.sku} — {product.name_display}
              </option>
            ))}
          </SelectField>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="quantity" type="number" min={0} step="0.001" label={t("contributions.field.quantity")} required
            value={values.quantity} onChange={(e) => update("quantity", e.target.value)}
          />
          <TextField
            id="unit_price" type="number" min={0} step="0.01" label={t("contributions.field.unit_price")} required
            value={values.unit_price} onChange={(e) => update("unit_price", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="contribution_date" type="date" label={t("contributions.field.contribution_date")}
            value={values.contribution_date} onChange={(e) => update("contribution_date", e.target.value)}
          />
          <TextField
            id="campaign" label={t("contributions.field.campaign")}
            value={values.campaign} onChange={(e) => update("campaign", e.target.value)}
            placeholder="2026"
          />
        </div>

        <TextareaField
          id="notes" label={t("contributions.field.notes")}
          value={values.notes} onChange={(e) => update("notes", e.target.value)}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/contributions")}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={isSubmitting || !values.member_id || !values.product_id}>
            {isSubmitting ? t("common.loading") : t("common.save")}
          </Button>
        </div>
      </form>
    </div>
  );
}
