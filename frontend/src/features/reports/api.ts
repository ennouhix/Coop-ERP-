import { apiClient } from "../../api/client";

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

export async function downloadMembersExcel(): Promise<void> {
  const response = await apiClient.get("/reporting/exports/members/", { responseType: "blob" });
  triggerBlobDownload(response.data, "membres.xlsx");
}

export async function downloadStockMovementsExcel(dateFrom?: string, dateTo?: string): Promise<void> {
  const params: Record<string, string> = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;

  const response = await apiClient.get("/reporting/exports/stock-movements/", {
    params,
    responseType: "blob",
  });
  triggerBlobDownload(response.data, "mouvements-stock.xlsx");
}

export async function downloadSalesOrdersExcel(dateFrom?: string, dateTo?: string): Promise<void> {
  const params: Record<string, string> = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;

  const response = await apiClient.get("/reporting/exports/sales-orders/", {
    params,
    responseType: "blob",
  });
  triggerBlobDownload(response.data, "commandes-vente.xlsx");
}
