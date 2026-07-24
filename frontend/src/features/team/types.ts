export type UserRole = "owner" | "admin" | "staff" | "accountant";
export type InvitationStatus = "pending" | "accepted" | "cancelled";

export interface TeamMember {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  phone_number: string;
  is_active: boolean;
  date_joined: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: UserRole;
  status: InvitationStatus;
  expires_at: string;
  created_at: string;
  invited_by_name: string;
}

export interface InviteFormValues {
  email: string;
  role: UserRole;
}

export interface AcceptInvitationValues {
  token: string;
  first_name: string;
  last_name: string;
  password: string;
}

export interface TeamMemberListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: TeamMember[];
}

export interface InvitationListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Invitation[];
}

export const ROLE_OPTIONS: UserRole[] = ["admin", "staff", "accountant"];
