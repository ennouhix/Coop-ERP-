import { ArrowLeft, Download, Plus, Calendar, User, Hash, CreditCard, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { OrderStatusBadge } from "../../shared/ui/OrderStatusBadge";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { cancelInvoice, downloadInvoicePdf, getInvoice, issueInvoice, recordPayment } from "./api";
import { EMPTY_PAYMENT_FORM, type Invoice, type PaymentFormValues, type PaymentMethod } from "./types";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

const PAYMENT_METHODS: PaymentMethod[] = ["cash", "bank_transfer", "check", "mobile_payment", "other"];

export function InvoiceDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const [isPaying, setIsPaying] = useState(false);
  const [paymentValues, setPaymentValues] = useState<PaymentFormValues>(EMPTY_PAYMENT_FORM);
  const [isDownloading, setIsDownloading] = useState(false);

  function load() {
    if (!id) return;
    setIsLoading(true);
    getInvoice(id).then(setInvoice).finally(() => setIsLoading(false));
  }

  useEffect(load, [id]);

  async function handleIssue() {
    if (!invoice) return;
    setError(null);
    setIsSubmittingAction(true);
    try {
      setInvoice(await issueInvoice(invoice.id));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmittingAction(false);
    }
  }

  async function handleCancel() {
    if (!invoice) return;
    setError(null);
    setIsSubmittingAction(true);
    try {
      setInvoice(await cancelInvoice(invoice.id));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmittingAction(false);
    }
  }

  function startPayment() {
    if (!invoice) return;
    setPaymentValues({ ...EMPTY_PAYMENT_FORM, amount: invoice.balance_due });
    setIsPaying(true);
  }

  async function handleSubmitPayment() {
    if (!invoice) return;
    setError(null);
    setIsSubmittingAction(true);
    try {
      await recordPayment(invoice.id, paymentValues);
      setIsPaying(false);
      load();
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmittingAction(false);
    }
  }

  async function handleDownloadPdf() {
    if (!invoice) return;
    setIsDownloading(true);
    try {
      await downloadInvoicePdf(invoice.id, invoice.invoice_number);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsDownloading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-terracotta-600 border-t-transparent"></div>
          <p className="mt-2 text-sm text-ink-700">{t("common.loading")}</p>
        </div>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-ink-300" />
          <p className="mt-2 text-sm text-terracotta-600">{t("billing.not_found")}</p>
        </div>
      </div>
    );
  }

  const canIssue = invoice.status === "draft";
  const canCancel = invoice.status === "draft" || invoice.status === "issued";
  const canPay = invoice.status === "issued" || invoice.status === "partially_paid";

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* En-tête avec navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/billing"
          className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-700 transition-colors hover:bg-sand-100 hover:text-ink-900"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("billing.back_to_list")}
        </Link>
        
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={handleDownloadPdf}
            disabled={isDownloading}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            {t("billing.download_pdf")}
          </Button>
        </div>
      </div>

      {/* Carte principale */}
      <div className="card">
        {/* En-tête de la facture */}
        <div className="border-b border-ink-200/50 bg-sand-50 px-6 py-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <span className="rounded-lg bg-sand-100 px-3 py-1 font-mono text-xs font-medium text-ink-700">
                  {invoice.invoice_number}
                </span>
                {invoice.is_overdue ? (
                  <StatusBadge label={t("billing.overdue")} tone="terracotta" />
                ) : (
                  <OrderStatusBadge status={invoice.status} i18nPrefix="billing" />
                )}
              </div>
              <h1 className="page-title">{invoice.customer_name}</h1>
            </div>
            
            <div className="flex flex-wrap items-center gap-2">
              {canCancel && (
                <Button variant="danger" onClick={handleCancel} disabled={isSubmittingAction}>
                  {t("billing.cancel_invoice")}
                </Button>
              )}
              {canIssue && (
                <Button onClick={handleIssue} disabled={isSubmittingAction}>
                  {t("billing.issue_invoice")}
                </Button>
              )}
              {canPay && !isPaying && (
                <Button onClick={startPayment} className="gap-2">
                  <Plus className="h-4 w-4" />
                  {t("billing.record_payment")}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Informations de la facture */}
        <div className="grid grid-cols-2 gap-6 border-b border-ink-200/50 px-6 py-4 md:grid-cols-4">
          <div>
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
              {t("billing.field.issue_date")}
            </p>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-ink-900">
              <Calendar className="h-4 w-4 text-ink-400" />
              {invoice.issue_date}
            </p>
          </div>
          <div>
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
              {t("billing.field.due_date")}
            </p>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-ink-900">
              <Calendar className="h-4 w-4 text-ink-400" />
              {invoice.due_date}
            </p>
          </div>
          <div>
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
              {t("billing.field.total")}
            </p>
            <p className="mt-1 text-lg font-semibold text-ink-900">
              {formatMoney(invoice.total_amount)}
            </p>
          </div>
          <div>
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
              {t("billing.field.balance_due")}
            </p>
            <p className={`mt-1 text-lg font-semibold ${invoice.balance_due === "0" ? "text-sage-600" : "text-terracotta-600"}`}>
              {formatMoney(invoice.balance_due)}
            </p>
          </div>
        </div>

        {/* Lignes de la facture */}
        <div className="px-6 py-4">
          <h2 className="mb-3 text-sm font-medium text-ink-700">
            {t("billing.items")}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-200 text-start font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
                  <th className="pb-2 pe-4">{t("billing.field.product")}</th>
                  <th className="pb-2 pe-4 text-end">{t("billing.field.quantity")}</th>
                  <th className="pb-2 pe-4 text-end">{t("billing.field.unit_price")}</th>
                  <th className="pb-2 text-end">{t("billing.field.line_total")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200/50">
                {invoice.lines.map((line) => (
                  <tr key={line.id}>
                    <td className="py-3 pe-4">
                      <div className="flex items-start gap-2">
                        <span className="font-mono text-xs text-ink-500">{line.product_sku}</span>
                        <span className="text-ink-900">{line.description}</span>
                      </div>
                    </td>
                    <td className="py-3 pe-4 text-end text-ink-700">{line.quantity}</td>
                    <td className="py-3 pe-4 text-end text-ink-700">{formatMoney(line.unit_price)}</td>
                    <td className="py-3 text-end font-medium text-ink-900">{formatMoney(line.line_total)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="border-t-2 border-ink-300">
                <tr>
                  <td colSpan={3} className="py-2 text-end font-medium text-ink-700">
                    {t("billing.field.total")}
                  </td>
                  <td className="py-2 text-end font-semibold text-ink-900">
                    {formatMoney(invoice.total_amount)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      {/* Messages d'erreur */}
      {error && (
        <div className="alert alert-error" role="alert">
          {error}
        </div>
      )}

      {/* Formulaire de paiement */}
      {isPaying && (
        <div className="card">
          <div className="border-b border-ink-200/50 bg-sand-50 px-6 py-3">
            <h2 className="flex items-center gap-2 text-sm font-medium text-ink-800">
              <CreditCard className="h-4 w-4" />
              {t("billing.record_payment")}
            </h2>
          </div>
          <div className="space-y-4 px-6 py-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <TextField
                id="payment_amount"
                type="number"
                min={0.01}
                step="0.01"
                label={t("billing.field.amount")}
                value={paymentValues.amount}
                onChange={(e) => setPaymentValues((p) => ({ ...p, amount: e.target.value }))}
                className="col-span-1"
              />
              <TextField
                id="payment_date"
                type="date"
                label={t("billing.field.payment_date")}
                value={paymentValues.payment_date}
                onChange={(e) => setPaymentValues((p) => ({ ...p, payment_date: e.target.value }))}
                className="col-span-1"
              />
              <SelectField
                id="payment_method"
                label={t("billing.field.payment_method")}
                value={paymentValues.payment_method}
                onChange={(e) => setPaymentValues((p) => ({ ...p, payment_method: e.target.value as PaymentMethod }))}
                className="col-span-1"
              >
                {PAYMENT_METHODS.map((m) => (
                  <option key={m} value={m}>{t(`billing.method_${m}`)}</option>
                ))}
              </SelectField>
            </div>
            <TextField
              id="payment_reference"
              label={t("billing.field.reference")}
              value={paymentValues.reference}
              onChange={(e) => setPaymentValues((p) => ({ ...p, reference: e.target.value }))}
              placeholder={t("billing.reference_placeholder")}
            />
            <div className="flex justify-end gap-2 border-t border-ink-200/50 pt-4">
              <Button
                variant="secondary"
                onClick={() => setIsPaying(false)}
                disabled={isSubmittingAction}
              >
                {t("common.cancel")}
              </Button>
              <Button
                onClick={handleSubmitPayment}
                disabled={isSubmittingAction}
              >
                {isSubmittingAction ? t("common.loading") : t("common.save")}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Historique des paiements */}
      {invoice.payments.length > 0 && (
        <div className="card">
          <div className="border-b border-ink-200/50 bg-sand-50 px-6 py-3">
            <h2 className="flex items-center gap-2 text-sm font-medium text-ink-800">
              <Hash className="h-4 w-4" />
              {t("billing.payments_title")}
            </h2>
          </div>
          <div className="px-6 py-4">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-ink-200 text-start font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
                    <th className="pb-2 pe-4">{t("billing.field.payment_date")}</th>
                    <th className="pb-2 pe-4 text-end">{t("billing.field.amount")}</th>
                    <th className="pb-2 pe-4">{t("billing.field.payment_method")}</th>
                    <th className="pb-2">{t("billing.field.reference")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-200/50">
                  {invoice.payments.map((payment) => (
                    <tr key={payment.id}>
                      <td className="py-3 pe-4 text-ink-700">{payment.payment_date}</td>
                      <td className="py-3 pe-4 text-end font-medium text-ink-900">
                        {formatMoney(payment.amount)}
                      </td>
                      <td className="py-3 pe-4 text-ink-700">
                        {t(`billing.method_${payment.payment_method}`)}
                      </td>
                      <td className="py-3 font-mono text-sm text-ink-600">
                        {payment.reference || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}