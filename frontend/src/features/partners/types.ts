export type PartnerStatus = "active" | "inactive";
export type PartnerKind = "individual" | "company";

export interface Partner {
  id: string;
  code: string;
  is_customer: boolean;
  is_supplier: boolean;
  partner_kind: PartnerKind;
  name: string;
  ice: string;
  phone_number: string;
  email: string;
  address: string;
  city: string;
  payment_terms_days: number;
  credit_limit: string;
  status: PartnerStatus;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface PartnerListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Partner[];
}

export interface PartnerFormValues {
  is_customer: boolean;
  is_supplier: boolean;
  partner_kind: PartnerKind;
  name: string;
  ice: string;
  phone_number: string;
  email: string;
  address: string;
  city: string;
  payment_terms_days: number;
  credit_limit: string;
  notes: string;
}

export const EMPTY_PARTNER_FORM: PartnerFormValues = {
  is_customer: true,
  is_supplier: false,
  partner_kind: "individual",
  name: "",
  ice: "",
  phone_number: "",
  email: "",
  address: "",
  city: "",
  payment_terms_days: 0,
  credit_limit: "0",
  notes: "",
};
