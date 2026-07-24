import { apiClient } from "../../api/client";
import type {
  Invoice, InvoiceListResponse, InvoiceStatus, ManualInvoiceCreateValues, Payment, PaymentFormValues,
} from "./types";

export interface InvoiceListParams {
  status?: InvoiceStatus | "";
  page?: number;
}

export async function listInvoices(params: InvoiceListParams): Promise<InvoiceListResponse> {
  const { data } = await apiClient.get<InvoiceListResponse>("/billing/invoices/", {
    params: { status: params.status || undefined, page: params.page },
  });
  return data;
}

export async function getInvoice(id: string): Promise<Invoice> {
  const { data } = await apiClient.get<Invoice>(`/billing/invoices/${id}/`);
  return data;
}

export async function createManualInvoice(values: ManualInvoiceCreateValues): Promise<Invoice> {
  const payload = {
    ...values,
    due_date: values.due_date || undefined,
    lines: values.lines.map((line) => ({
      product_id: line.product_id,
      description: line.description,
      quantity: line.quantity,
      unit_price: line.unit_price,
    })),
  };
  const { data } = await apiClient.post<Invoice>("/billing/invoices/", payload);
  return data;
}

export async function createInvoiceFromOrder(
  orderId: string, issueDate: string, dueDate?: string
): Promise<Invoice> {
  const { data } = await apiClient.post<Invoice>("/billing/invoices/from-order/", {
    order_id: orderId, issue_date: issueDate, due_date: dueDate || undefined,
  });
  return data;
}

export async function issueInvoice(id: string): Promise<Invoice> {
  const { data } = await apiClient.post<Invoice>(`/billing/invoices/${id}/issue/`);
  return data;
}

export async function cancelInvoice(id: string): Promise<Invoice> {
  const { data } = await apiClient.post<Invoice>(`/billing/invoices/${id}/cancel/`);
  return data;
}

export async function recordPayment(id: string, values: PaymentFormValues): Promise<Payment> {
  const { data } = await apiClient.post<Payment>(`/billing/invoices/${id}/payments/`, values);
  return data;
}

/** Télécharge la facture PDF (Epic 13) et déclenche le téléchargement navigateur. */
export async function downloadInvoicePdf(id: string, invoiceNumber: string): Promise<void> {
  const response = await apiClient.get(`/reporting/invoices/${id}/pdf/`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = `${invoiceNumber}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
