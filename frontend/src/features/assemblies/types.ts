export type AssemblyType = "ordinary" | "extraordinary";
export type AssemblyStatus = "draft" | "scheduled" | "done" | "cancelled";
export type AttendanceStatus = "present" | "absent" | "excused";
export type VoteChoice = "for" | "against" | "abstention";

export interface Assembly {
  id: string;
  title: string;
  assembly_type: AssemblyType;
  scheduled_date: string;
  location: string;
  quorum_percent: string;
  agenda: string;
  status: AssemblyStatus;
  minutes_notes: string;
  attendances_count: number;
  present_count: number;
  created_at: string;
  updated_at: string;
}

export interface AssemblyAttendance {
  id: string;
  assembly: string;
  member: string;
  member_name: string;
  member_number: string;
  attendance_status: AttendanceStatus;
  vote: VoteChoice | null;
  created_at: string;
}

export interface AssemblyListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Assembly[];
}

export interface AssemblyAttendanceListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AssemblyAttendance[];
}

export interface AssemblyFormValues {
  title: string;
  assembly_type: AssemblyType;
  scheduled_date: string;
  location: string;
  quorum_percent: string;
  agenda: string;
  status: AssemblyStatus;
  minutes_notes: string;
}

export interface AttendanceFormValues {
  member_id: string;
  attendance_status: AttendanceStatus;
  vote: VoteChoice | "";
}

export const EMPTY_ASSEMBLY_FORM: AssemblyFormValues = {
  title: "",
  assembly_type: "ordinary",
  scheduled_date: new Date().toISOString().slice(0, 10),
  location: "",
  quorum_percent: "50.00",
  agenda: "",
  status: "draft",
  minutes_notes: "",
};

export const EMPTY_ATTENDANCE_FORM: AttendanceFormValues = {
  member_id: "",
  attendance_status: "present",
  vote: "",
};
