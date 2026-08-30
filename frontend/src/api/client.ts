export interface HealthResponse {
  status: string;
  version: string;
  llm_enabled: boolean;
}

export const TAXONOMY = [
  "groceries",
  "dining",
  "coffee",
  "transport",
  "fuel",
  "utilities",
  "rent_mortgage",
  "subscriptions",
  "shopping",
  "health",
  "entertainment",
  "income",
  "other",
] as const;

export type Category = (typeof TAXONOMY)[number];

export interface ImportSummary {
  import_id: string;
  filename: string;
  rows_received: number;
  rows_accepted: number;
  rows_deduped: number;
  date_range: [string, string];
  category_breakdown: Record<Category, number>;
  llm_fallback_count: number;
}

export interface ImportListItem {
  import_id: string;
  filename: string;
  rows_accepted: number;
  imported_at: string;
  date_range: [string, string];
}

export interface Transaction {
  id: string;
  txn_date: string;
  description_raw: string;
  merchant: string;
  amount: number;
  category: Category;
  category_confidence: number;
  category_source: "model" | "rule" | "user";
  is_recurring: boolean;
  recurring_group_id: string | null;
  is_anomaly: boolean;
  anomaly_reason: string | null;
}

export interface TransactionsResponse {
  total: number;
  limit: number;
  offset: number;
  transactions: Transaction[];
}

export interface CategoryTotal {
  category: Category;
  total: number;
  txn_count: number;
}

export interface MonthlyTotal {
  month: string;
  spend: number;
  income: number;
}

export interface MerchantTotal {
  merchant: string;
  total: number;
  txn_count: number;
}

export interface Summary {
  range: [string | null, string | null];
  totals: { spend: number; income: number; net: number };
  by_category: CategoryTotal[];
  monthly: MonthlyTotal[];
  top_merchants: MerchantTotal[];
}

export interface Subscription {
  recurring_group_id: string;
  merchant: string;
  cadence: "weekly" | "biweekly" | "monthly" | "quarterly" | "annual";
  avg_amount: number;
  amount_stddev: number;
  monthly_cost: number;
  first_seen: string;
  last_seen: string;
  next_expected: string;
  occurrences: number;
  active: boolean;
  price_changed: boolean;
}

export interface SubscriptionsResponse {
  subscriptions: Subscription[];
  total_monthly_cost: number;
  total_annual_cost: number;
}

export interface Alert {
  transaction_id: string;
  txn_date: string;
  description_raw: string;
  amount: number;
  category: Category;
  reason: string;
  signals: string[];
}

export interface AlertsResponse {
  alerts: Alert[];
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = init ? await fetch(url, init) : await fetch(url);
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(body.detail ?? `API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/healthz");
}

export async function uploadImport(
  file: File,
  mapping?: Record<string, string>,
): Promise<ImportSummary> {
  const body = new FormData();
  body.append("file", file);
  if (mapping && Object.keys(mapping).length > 0) body.append("mapping", JSON.stringify(mapping));
  return request<ImportSummary>("/api/imports", { method: "POST", body });
}

export async function listImports(): Promise<{ imports: ImportListItem[] }> {
  return request<{ imports: ImportListItem[] }>("/api/imports");
}

export interface TransactionFilters {
  from?: string;
  to?: string;
  category?: Category;
  merchant?: string;
  is_recurring?: boolean;
  is_anomaly?: boolean;
  limit?: number;
  offset?: number;
  sort?: "date" | "amount" | "-date" | "-amount";
}

export async function listTransactions(
  filters: TransactionFilters = {},
): Promise<TransactionsResponse> {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined) query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<TransactionsResponse>(`/api/transactions${suffix}`);
}

export async function updateTransactionCategory(
  id: string,
  category: Category,
): Promise<Transaction> {
  return request<Transaction>(`/api/transactions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category }),
  });
}

export async function getSummary(from?: string, to?: string): Promise<Summary> {
  const query = new URLSearchParams();
  if (from) query.set("from", from);
  if (to) query.set("to", to);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<Summary>(`/api/analytics/summary${suffix}`);
}

export async function listSubscriptions(): Promise<SubscriptionsResponse> {
  return request<SubscriptionsResponse>("/api/subscriptions");
}

export async function listAlerts(from?: string): Promise<AlertsResponse> {
  const suffix = from ? `?from=${encodeURIComponent(from)}` : "";
  return request<AlertsResponse>(`/api/alerts${suffix}`);
}
