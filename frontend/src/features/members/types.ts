export type MemberStatus = "active" | "suspended" | "inactive";
export type MemberType = "individual" | "entity";

export interface Member {
  id: string;
  member_number: string;
  member_type: MemberType;
  first_name: string;
  last_name: string;
  full_name: string;
  cin: string;
  phone_number: string;
  email: string;
  address: string;
  city: string;
  birth_date: string | null;
  join_date: string;
  status: MemberStatus;
  shares_count: number;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface MemberListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Member[];
}

export interface MemberFormValues {
  member_type: MemberType;
  first_name: string;
  last_name: string;
  cin: string;
  phone_number: string;
  email: string;
  address: string;
  city: string;
  birth_date: string;
  join_date: string;
  shares_count: number;
  notes: string;
}

export const EMPTY_MEMBER_FORM: MemberFormValues = {
  member_type: "individual",
  first_name: "",
  last_name: "",
  cin: "",
  phone_number: "",
  email: "",
  address: "",
  city: "",
  birth_date: "",
  join_date: new Date().toISOString().slice(0, 10),
  shares_count: 0,
  notes: "",
};
