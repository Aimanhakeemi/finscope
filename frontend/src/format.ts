import type { Category } from "./api/client";

const CATEGORY_LABELS: Record<Category, string> = {
  groceries: "Groceries",
  dining: "Dining",
  coffee: "Coffee",
  transport: "Transport",
  fuel: "Fuel",
  utilities: "Utilities",
  rent_mortgage: "Rent / mortgage",
  subscriptions: "Subscriptions",
  shopping: "Shopping",
  health: "Health",
  entertainment: "Entertainment",
  income: "Income",
  other: "Other",
};

const SIGNAL_LABELS: Record<string, string> = {
  robust_z: "Statistical outlier",
  iqr: "Outside normal range",
  new_large_merchant: "New large merchant",
};

export function humanizeCategory(category: string): string {
  const knownLabel = CATEGORY_LABELS[category as Category];
  if (knownLabel) return knownLabel;
  return category.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

export function humanizeSignal(signal: string): string {
  const knownLabel = SIGNAL_LABELS[signal];
  if (knownLabel) return knownLabel;
  return signal.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

export function formatDate(value: string | null): string {
  if (!value) return "";
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.valueOf())) return value;
  return parsed.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}
