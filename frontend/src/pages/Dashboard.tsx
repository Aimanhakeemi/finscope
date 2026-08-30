import { useEffect, useState } from "react";
import { getSummary, listTransactions, updateTransactionCategory, type Category, type Summary, type Transaction } from "../api/client";
import CategoryBarChart from "../components/CategoryBarChart";
import DataTable from "../components/DataTable";
import MonthlyTrendChart from "../components/MonthlyTrendChart";

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void Promise.all([getSummary(), listTransactions({ limit: 100, sort: "-date" })])
      .then(([nextSummary, nextTransactions]) => {
        setSummary(nextSummary);
        setTransactions(nextTransactions.transactions);
      })
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Dashboard failed to load."));
  }, []);

  async function changeCategory(id: string, category: Category) {
    try {
      const updated = await updateTransactionCategory(id, category);
      setTransactions((current) => current.map((item) => (item.id === id ? updated : item)));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update category.");
    }
  }

  if (error) return <p role="alert" className="text-rose-400">{error}</p>;
  if (!summary) return <p className="text-slate-400">Loading dashboard…</p>;

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <p className="mt-2 text-slate-400">Your spending at a glance.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {Object.entries(summary.totals).map(([label, value]) => (
          <div key={label} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <p className="text-sm capitalize text-slate-400">{label}</p>
            <p className="mt-2 text-2xl font-semibold">${value.toFixed(2)}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <CategoryBarChart data={summary.by_category} />
        <MonthlyTrendChart data={summary.monthly} />
      </div>
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h2 className="mb-4 text-lg font-medium">Top merchants</h2>
        <div className="space-y-3">
          {summary.top_merchants.map((merchant) => {
            const width = Math.max(5, Math.round((Math.abs(merchant.total) / Math.max(1, Math.abs(summary.top_merchants[0]?.total ?? 1))) * 100));
            return <div key={merchant.merchant}><div className="mb-1 flex justify-between text-sm"><span>{merchant.merchant}</span><span>${Math.abs(merchant.total).toFixed(2)}</span></div><div className="h-2 rounded bg-slate-800"><div className="h-2 rounded bg-violet-400" style={{ width: `${width}%` }} /></div></div>;
          })}
        </div>
      </div>
      <div>
        <h2 className="mb-3 text-lg font-medium">Recent transactions</h2>
        <DataTable transactions={transactions} onCategoryChange={changeCategory} />
      </div>
    </section>
  );
}
