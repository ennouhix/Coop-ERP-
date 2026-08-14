import { apiClient } from "../../api/client";
import type {
  Account,
  AccountCreateInput,
  AccountingDashboardData,
  AccountingEntry,
  AccountingEntryListResponse,
  AccountListResponse,
  EntryCreateValues,
  FinancialStatementsResponse,
  GeneralLedgerResponse,
  Journal,
  JournalListResponse,
  TrialBalanceResponse,
} from "./types";

// ---- Tableau de bord ----
export async function getAccountingDashboard(): Promise<AccountingDashboardData> {
  const { data } = await apiClient.get<AccountingDashboardData>("/accounting/dashboard/");
  return data;
}

// ---- Plan comptable ----
export async function listAccounts(params?: { account_type?: string }): Promise<Account[]> {
  const { data } = await apiClient.get<AccountListResponse>("/accounting/accounts/", { params });
  return data.results;
}

export async function createAccount(input: AccountCreateInput): Promise<Account> {
  const { data } = await apiClient.post<Account>("/accounting/accounts/", input);
  return data;
}

// ---- Journaux ----
export async function listJournals(): Promise<Journal[]> {
  const { data } = await apiClient.get<JournalListResponse>("/accounting/journals/");
  return data.results;
}

// ---- Écritures comptables ----
export interface EntryListParams {
  journal?: string;
  is_posted?: boolean | "";
  period?: string;
  page?: number;
}

export async function listEntries(params: EntryListParams): Promise<AccountingEntryListResponse> {
  const { data } = await apiClient.get<AccountingEntryListResponse>("/accounting/entries/", {
    params: {
      journal: params.journal || undefined,
      is_posted: params.is_posted === "" ? undefined : params.is_posted,
      period: params.period || undefined,
      page: params.page,
    },
  });
  return data;
}

export async function getEntry(id: string): Promise<AccountingEntry> {
  const { data } = await apiClient.get<AccountingEntry>(`/accounting/entries/${id}/`);
  return data;
}

export async function createEntry(values: EntryCreateValues): Promise<AccountingEntry> {
  const { data } = await apiClient.post<AccountingEntry>("/accounting/entries/", values);
  return data;
}

export async function postEntry(id: string): Promise<AccountingEntry> {
  const { data } = await apiClient.post<AccountingEntry>(`/accounting/entries/${id}/post/`);
  return data;
}

// ---- Grand livre ----
export interface LedgerParams {
  account_id: string;
  date_from?: string;
  date_to?: string;
}

export async function getGeneralLedger(params: LedgerParams): Promise<GeneralLedgerResponse> {
  const { data } = await apiClient.get<GeneralLedgerResponse>("/accounting/ledger/", {
    params: {
      account_id: params.account_id,
      date_from: params.date_from || undefined,
      date_to: params.date_to || undefined,
    },
  });
  return data;
}

// ---- Balance des comptes ----
export async function getTrialBalance(params?: { period?: string }): Promise<TrialBalanceResponse> {
  const { data } = await apiClient.get<TrialBalanceResponse>("/accounting/trial-balance/", {
    params: { period: params?.period || undefined },
  });
  return data;
}

// ---- États financiers (CPC & Bilan) ----
export async function getFinancialStatements(params?: { period?: string }): Promise<FinancialStatementsResponse> {
  const { data } = await apiClient.get<FinancialStatementsResponse>("/accounting/financial-statements/", {
    params: { period: params?.period || undefined },
  });
  return data;
}

