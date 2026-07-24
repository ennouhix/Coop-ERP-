export interface Cooperative {
  id: string;
  name: string;
  slug: string;
  logo: string | null;
  legal_name: string;
  ice: string;
  rc_number: string;
  email: string;
  phone_number: string;
  address: string;
  city: string;
  region: string;
  default_language: string;
  subscription_plan: string;
  subscription_status: string;
  trial_ends_at: string | null;
  is_trial_expired: boolean;
  created_at: string;
}

export type CooperativeFormValues = Pick<
  Cooperative,
  | "name"
  | "legal_name"
  | "ice"
  | "rc_number"
  | "email"
  | "phone_number"
  | "address"
  | "city"
  | "region"
  | "default_language"
>;
