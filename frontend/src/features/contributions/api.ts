import { apiClient } from "../../api/client";
import type {
  Contribution,
  ContributionFormValues,
  ContributionListResponse,
  ContributionStatus,
} from "./types";

export interface ContributionListParams {
  status?: ContributionStatus | "";
  page?: number;
}

export async function listContributions(
  params: ContributionListParams = {},
): Promise<ContributionListResponse> {
  const { data } = await apiClient.get<ContributionListResponse>("/contributions/", {
    params: { status: params.status || undefined, page: params.page },
  });
  return data;
}

export async function getContribution(id: string): Promise<Contribution> {
  const { data } = await apiClient.get<Contribution>(`/contributions/${id}/`);
  return data;
}

export async function createContribution(values: ContributionFormValues): Promise<Contribution> {
  const { data } = await apiClient.post<Contribution>("/contributions/", {
    ...values,
    contribution_date: values.contribution_date || undefined,
  });
  return data;
}

export async function markContributionPaid(id: string): Promise<Contribution> {
  const { data } = await apiClient.post<Contribution>(`/contributions/${id}/mark-paid/`);
  return data;
}
