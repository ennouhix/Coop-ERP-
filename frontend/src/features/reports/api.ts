import { apiClient } from "../../api/client";

export type ReportOutput = "xlsx" | "pdf";

export interface ReportFilters {
  date_from?: string;
  date_to?: string;
  movement_type?: string;
  warehouse_id?: string;
  status?: string;
  customer_id?: string;
  supplier_id?: string;
  kind?: string;
  period?: string;
  journal_id?: string;
}

export interface ReportPreview {
  report: string;
  columns: string[];
  rows: string[][];
  total: number;
  truncated: boolean;
}

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

function buildParams(filters: ReportFilters): Record<string, string> {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== "")
  ) as Record<string, string>;
}

export async function downloadReport(
  slug: string,
  filename: string,
  output: ReportOutput,
  filters: ReportFilters = {}
): Promise<void> {
  const response = await apiClient.get(`/reporting/exports/${slug}/`, {
    params: { ...buildParams(filters), output },
    responseType: "blob",
  });
  triggerBlobDownload(response.data, `${filename}.${output}`);
}

export async function fetchReportPreview(
  slug: string,
  filters: ReportFilters = {}
): Promise<ReportPreview> {
  const { data } = await apiClient.get<ReportPreview>(`/reporting/previews/${slug}/`, {
    params: buildParams(filters),
  });
  return data;
}
