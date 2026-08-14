import { apiClient } from "../../api/client";
import type { DocumentTemplate, DocumentTemplateFormValues, DocumentTemplateTypeValue } from "./types";

function triggerBlobDownload(data: Blob, filename: string): void {
  const url = window.URL.createObjectURL(new Blob([data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

async function downloadDocument(path: string, filename: string): Promise<void> {
  const response = await apiClient.get(path, { responseType: "blob" });
  triggerBlobDownload(response.data, filename);
}

export async function downloadDeliveryNote(orderId: string, orderNumber: string): Promise<void> {
  await downloadDocument(`/documents/delivery-notes/${orderId}/pdf/`, `bon-livraison_${orderNumber}.pdf`);
}

export async function downloadPurchaseOrder(orderId: string, orderNumber: string): Promise<void> {
  await downloadDocument(`/documents/purchase-orders/${orderId}/pdf/`, `bon-commande_${orderNumber}.pdf`);
}

export async function downloadReceipt(orderId: string, orderNumber: string): Promise<void> {
  await downloadDocument(`/documents/receipts/${orderId}/pdf/`, `bon-reception_${orderNumber}.pdf`);
}

export async function getDocumentTemplates(): Promise<DocumentTemplate[]> {
  const { data } = await apiClient.get<DocumentTemplate[]>("/documents/templates/");
  return data;
}

export async function updateDocumentTemplate(
  templateType: DocumentTemplateTypeValue, values: DocumentTemplateFormValues
): Promise<DocumentTemplate> {
  const { data } = await apiClient.put<DocumentTemplate>(`/documents/templates/${templateType}/`, values);
  return data;
}
