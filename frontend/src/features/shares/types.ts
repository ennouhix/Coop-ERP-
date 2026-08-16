export type ShareTransactionType = "subscription" | "redemption";

export interface ShareTransaction {
  id: string;
  member: string;
  member_name: string;
  transaction_type: ShareTransactionType;
  shares_count: number;
  amount_per_share: string;
  total_amount: string;
  transaction_date: string;
  notes: string;
  created_at: string;
}

export interface ShareTransactionListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ShareTransaction[];
}

export interface ShareTransactionFormValues {
  member_id: string;
  transaction_type: ShareTransactionType;
  shares_count: number;
  amount_per_share: string;
  transaction_date: string;
  notes: string;
}

export const EMPTY_SHARE_TRANSACTION_FORM: ShareTransactionFormValues = {
  member_id: "",
  transaction_type: "subscription",
  shares_count: 1,
  amount_per_share: "100.00",
  transaction_date: new Date().toISOString().slice(0, 10),
  notes: "",
};
