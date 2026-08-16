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

export interface CooperativeEmailConfig {
  id: string;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_use_tls: boolean;
  from_name: string;
  from_email: string;
  is_configured: boolean;
}

export interface EmailNotification {
  id: string;
  notification_type: string;
  notification_type_display: string;
  recipient_email: string;
  recipient_name: string;
  subject: string;
  status: string;
  status_display: string;
  error_message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}
