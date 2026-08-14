// Types du module Comptabilité / Trésorerie

export type AccountType = "asset" | "liability" | "equity" | "revenue" | "expense" | "treasury";
export type JournalType = "sales" | "purchases" | "cash" | "bank" | "general";

export interface Account {
  id: string;
  code: string;
  name: { fr: string; ar: string };
  name_display: string;
  account_type: AccountType;
  parent: string | null;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Account[];
}

export interface Journal {
  id: string;
  code: string;
  name: { fr: string; ar: string };
  name_display: string;
  journal_type: JournalType;
}

export interface JournalListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Journal[];
}

export interface AccountingEntryLine {
  id: string;
  account: string;
  account_code: string;
  account_name: string;
  label: string;
  debit: string;
  credit: string;
}

export interface AccountingEntry {
  id: string;
  journal: string;
  journal_code: string;
  entry_number: string;
  entry_date: string;
  period: string;
  description: string;
  is_posted: boolean;
  lines: AccountingEntryLine[];
  total_debit: string;
  total_credit: string;
  is_balanced: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountingEntryListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AccountingEntry[];
}

export interface GeneralLedgerRow {
  entry_number: string;
  entry_date: string;
  journal_code: string;
  description: string;
  debit: string;
  credit: string;
  running_balance: string;
}

export interface GeneralLedgerResponse {
  account: Account;
  rows: GeneralLedgerRow[];
}

export interface TrialBalanceRow {
  account_code: string;
  account_name: string | { fr: string; ar: string };
  debit_total: string;
  credit_total: string;
  debit_balance: string;
  credit_balance: string;
}

export interface TrialBalanceResponse {
  period: string | null;
  rows: TrialBalanceRow[];
  total_debit: string;
  total_credit: string;
}

export interface AccountCreateInput {
  code: string;
  name: string | { fr: string; ar?: string };
  account_type: AccountType;
  parent?: string | null;
}

export interface AccountingDashboardData {
  revenue_total: string;
  expense_total: string;
  net_result: string;
  treasury_balance: string;
  draft_entries_count: number;
  posted_entries_count: number;
  recent_entries: AccountingEntry[];
}

export interface FinancialStatementItem {
  account_code: string;
  account_name: string | { fr: string; ar?: string };
  debit: string;
  credit: string;
  net_amount: string;
}

export interface CPCData {
  revenues: FinancialStatementItem[];
  expenses: FinancialStatementItem[];
  total_revenue: string;
  total_expense: string;
  net_result: string;
}

export interface BilanData {
  assets: FinancialStatementItem[];
  liabilities: FinancialStatementItem[];
  equity: FinancialStatementItem[];
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  total_passif_and_equity: string;
}

export interface FinancialStatementsResponse {
  period: string | null;
  cpc: CPCData;
  bilan: BilanData;
}

export interface LineInput {
  account_id: string;
  label: string;
  debit: string;
  credit: string;
}

export const EMPTY_LINE: LineInput = { account_id: "", label: "", debit: "0.00", credit: "0.00" };

export interface EntryCreateValues {
  journal_id: string;
  entry_date: string;
  description: string;
  lines: LineInput[];
}

export const EMPTY_ENTRY_FORM: EntryCreateValues = {
  journal_id: "",
  entry_date: new Date().toISOString().slice(0, 10),
  description: "",
  lines: [{ ...EMPTY_LINE }, { ...EMPTY_LINE }],
};

