import { apiClient } from "../../api/client";
import type {
  Assembly,
  AssemblyAttendance,
  AssemblyAttendanceListResponse,
  AssemblyFormValues,
  AssemblyListResponse,
  AssemblyStatus,
  AttendanceFormValues,
} from "./types";

export interface AssemblyListParams {
  status?: AssemblyStatus | "";
  page?: number;
}

export async function listAssemblies(params: AssemblyListParams = {}): Promise<AssemblyListResponse> {
  const { data } = await apiClient.get<AssemblyListResponse>("/assemblies/", {
    params: { status: params.status || undefined, page: params.page },
  });
  return data;
}

export async function getAssembly(id: string): Promise<Assembly> {
  const { data } = await apiClient.get<Assembly>(`/assemblies/${id}/`);
  return data;
}

export async function createAssembly(values: AssemblyFormValues): Promise<Assembly> {
  const { data } = await apiClient.post<Assembly>("/assemblies/", values);
  return data;
}

export async function updateAssembly(id: string, values: Partial<AssemblyFormValues>): Promise<Assembly> {
  const { data } = await apiClient.patch<Assembly>(`/assemblies/${id}/`, values);
  return data;
}

export async function listAssemblyAttendances(
  assemblyId: string,
): Promise<AssemblyAttendanceListResponse> {
  const { data } = await apiClient.get<AssemblyAttendanceListResponse>(
    `/assemblies/${assemblyId}/attendance/`,
  );
  return data;
}

export async function registerAttendance(
  assemblyId: string,
  values: AttendanceFormValues,
): Promise<AssemblyAttendance> {
  const payload: Record<string, string> = {
    member_id: values.member_id,
    attendance_status: values.attendance_status,
  };
  if (values.vote) payload.vote = values.vote;
  const { data } = await apiClient.post<AssemblyAttendance>(
    `/assemblies/${assemblyId}/attendance/`,
    payload,
  );
  return data;
}
