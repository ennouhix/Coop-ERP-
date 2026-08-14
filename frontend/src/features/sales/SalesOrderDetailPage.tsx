import { ArrowLeft, FileDown, Truck } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { OrderStatusBadge } from "../../shared/ui/OrderStatusBadge";
import { downloadDeliveryNote } from "../documents/api";
import { cancelSalesOrder, confirmSalesOrder, deliverSalesOrder, getSalesOrder } from "./api";
import type { SalesOrder } from "./types";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function SalesOrderDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const [order, setOrder] = useState<SalesOrder | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDelivering, setIsDelivering] = useState(false);
  const [deliveryQuantities, setDeliveryQuantities] = useState<Record<string, string>>({});
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  function load() {
    if (!id) return;
    setIsLoading(true);
    getSalesOrder(id).then(setOrder).finally(() => setIsLoading(false));
  }

  useEffect(load, [id]);

  async function handleConfirm() {
    if (!order) return;
    setError(null);
    setIsSubmittingAction(true);
    try {
      setOrder(await confirmSalesOrder(order.id));
    } catch (err) {
      // Peut échouer si la confirmation dépasserait la limite de crédit
      // du client (Epic 10) — le message backend explicite remonte tel quel.
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmittingAction(false);
    }
  }

  async function handleCancel() {
    if (!order) return;
    setError(null);
    setIsSubmittingAction(true);
    try {
      setOrder(await cancelSalesOrder(order.id));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmittingAction(false);
    }
  }

  async function handleDownloadDeliveryNote() {
    if (!order) return;
    setError(null);
    setIsDownloadingPdf(true);
    try {
      await downloadDeliveryNote(order.id, order.order_number);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsDownloadingPdf(false);
    }
  }

  function startDelivering() {
    if (!order) return;
    const defaults: Record<string, string> = {};
    order.lines.forEach((line) => {
      defaults[line.id] = line.quantity_remaining;
    });
    setDeliveryQuantities(defaults);
    setIsDelivering(true);
  }

  async function handleSubmitDelivery() {
    if (!order) return;
    setError(null);
    const deliveries = Object.entries(deliveryQuantities)
      .filter(([, qty]) => Number(qty) > 0)
      .map(([line_id, quantity]) => ({ line_id, quantity }));

    if (deliveries.length === 0) {
      setError(t("sales.error_delivery_required"));
      return;
    }

    setIsSubmittingAction(true);
    try {
      // Peut échouer si le stock disponible ne suffit plus (Epic 8) —
      // aucune vente à découvert n'est permise, le message remonte tel quel.
      const updated = await deliverSalesOrder(order.id, deliveries);
      setOrder(updated);
      setIsDelivering(false);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmittingAction(false);
    }
  }

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  if (!order) return <p className="text-sm text-terracotta-600">{t("sales.not_found")}</p>;

  const canConfirm = order.status === "draft";
  const canCancel = order.status === "draft" || order.status === "confirmed";
  const canDeliver = order.status === "confirmed" || order.status === "partially_delivered";
  const canDownloadDeliveryNote = order.status !== "draft" && order.status !== "cancelled";

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/sales" className="inline-flex items-center gap-1.5 text-sm text-ink-700 hover:text-ink-900">
        <ArrowLeft className="h-4 w-4" />
        {t("sales.back_to_list")}
      </Link>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-ink-700/70">{order.order_number}</p>
          <h1 className="page-title">{order.customer_name}</h1>
        </div>
        <div className="flex items-center gap-2">
          <OrderStatusBadge status={order.status} i18nPrefix="sales" />
          {canCancel && (
            <Button variant="danger" onClick={handleCancel} disabled={isSubmittingAction}>
              {t("sales.cancel_order")}
            </Button>
          )}
          {canConfirm && (
            <Button onClick={handleConfirm} disabled={isSubmittingAction}>
              {t("sales.confirm_order")}
            </Button>
          )}
          {canDeliver && !isDelivering && (
            <Button onClick={startDelivering}>
              <Truck className="h-4 w-4" />
              {t("sales.deliver_order")}
            </Button>
          )}
          {canDownloadDeliveryNote && (
            <Button variant="secondary" onClick={handleDownloadDeliveryNote} disabled={isDownloadingPdf}>
              <FileDown className="h-4 w-4" />
              {t("sales.download_delivery_note")}
            </Button>
          )}
        </div>
      </div>

      {error && <p role="alert" className="mt-3 text-start text-sm text-terracotta-600">{error}</p>}

      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div><span className="text-ink-700/70">{t("sales.field.warehouse")} : </span><span className="text-ink-900">{order.warehouse_code}</span></div>
        <div><span className="text-ink-700/70">{t("sales.field.order_date")} : </span><span className="text-ink-900">{order.order_date}</span></div>
        <div><span className="text-ink-700/70">{t("sales.total")} : </span><span className="font-semibold text-ink-900">{formatMoney(order.total_amount)}</span></div>
      </div>

      <div className="mt-6 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("sales.field.product")}</th>
              <th className="px-4 py-3 text-start">{t("sales.field.quantity")}</th>
              <th className="px-4 py-3 text-start">{t("sales.field.delivered")}</th>
              <th className="px-4 py-3 text-start">{t("sales.field.unit_price")}</th>
              <th className="px-4 py-3 text-start">{t("sales.field.line_total")}</th>
              {isDelivering && <th className="px-4 py-3 text-start">{t("sales.field.deliver_now")}</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {order.lines.map((line) => (
              <tr key={line.id}>
                <td className="px-4 py-3">
                  <span className="font-mono text-xs text-ink-700">{line.product_sku}</span> {line.product_name}
                </td>
                <td className="px-4 py-3 text-ink-700">{line.quantity_ordered}</td>
                <td className="px-4 py-3 text-ink-700">{line.quantity_delivered}</td>
                <td className="px-4 py-3 text-ink-700">{formatMoney(line.unit_price)}</td>
                <td className="px-4 py-3 font-medium text-ink-900">{formatMoney(line.line_total)}</td>
                {isDelivering && (
                  <td className="px-4 py-3">
                    <input
                      type="number" min={0} max={Number(line.quantity_remaining)} step="0.001"
                      value={deliveryQuantities[line.id] ?? ""}
                      onChange={(e) => setDeliveryQuantities((prev) => ({ ...prev, [line.id]: e.target.value }))}
                      disabled={Number(line.quantity_remaining) <= 0}
                      className="w-24 rounded-md border border-ink-900/15 px-2 py-1 text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
                    />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isDelivering && (
        <div className="mt-3 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setIsDelivering(false)}>{t("common.cancel")}</Button>
          <Button onClick={handleSubmitDelivery} disabled={isSubmittingAction}>
            {isSubmittingAction ? t("common.loading") : t("sales.confirm_delivery")}
          </Button>
        </div>
      )}

      {order.notes && (
        <p className="mt-4 text-sm text-ink-700"><span className="font-medium">{t("sales.field.notes")} : </span>{order.notes}</p>
      )}
    </div>
  );
}
