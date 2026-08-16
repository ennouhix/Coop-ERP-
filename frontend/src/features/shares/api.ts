import { apiClient } from "../../api/client";
import type {
  ShareTransaction,
  ShareTransactionFormValues,
  ShareTransactionListResponse,
  ShareTransactionType,
} from "./types";

export interface ShareTransactionListParams {
  transaction_type?: ShareTransactionType | "";
  page?: number;
}

export async function listShareTransactions(
  params: ShareTransactionListParams = {},
): Promise<ShareTransactionListResponse> {
  const { data } = await apiClient.get<ShareTransactionListResponse>("/members/shares/", {
    params: {
      transaction_type: params.transaction_type || undefined,
      page: params.page,
    },
  });
  return data;
}

export async function getShareTransaction(id: string): Promise<ShareTransaction> {
  const { data } = await apiClient.get<ShareTransaction>(`/members/shares/${id}/`);
  return data;
}

export async function createShareTransaction(values: ShareTransactionFormValues): Promise<ShareTransaction> {
  const { data } = await apiClient.post<ShareTransaction>("/members/shares/", {
    ...values,
    transaction_date: values.transaction_date || undefined,
  });
  return data;
}
