export type ContributionStatus = "pending" | "paid";

export interface Contribution {
  id: string;
  member: string;
  member_name: string;
  product: string;
  product_name: string;
  product_sku: string;
  quantity: string;
  unit_price: string;
  total_amount: string;
  contribution_date: string;
  campaign: string;
  status: ContributionStatus;
  payment_date: string | null;
  notes: string;
  created_at: string;
}

export interface ContributionListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Contribution[];
}

export interface ContributionFormValues {
  member_id: string;
  product_id: string;
  quantity: string;
  unit_price: string;
  contribution_date: string;
  campaign: string;
  notes: string;
}

export const EMPTY_CONTRIBUTION_FORM: ContributionFormValues = {
  member_id: "",
  product_id: "",
  quantity: "",
  unit_price: "",
  contribution_date: new Date().toISOString().slice(0, 10),
  campaign: "",
  notes: "",
};
