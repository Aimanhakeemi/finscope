import { useEffect, useRef, useState } from "react";
import { getForecast, getSummary, listTransactions, updateTransactionCategory, type Category, type ForecastResponse, type Summary, type Transaction } from "../api/client";
import CategoryBarChart from "../components/CategoryBarChart";
import DataTable from "../components/DataTable";
import ForecastCard from "../components/ForecastCard";
import MonthlyTrendChart from "../components/MonthlyTrendChart";

function formatAmount(value: number, positiveSign = false): string {
  const amount = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  if (value < 0) return `− $${amount}`;
  return `${positiveSign && value > 0 ? "+ " : ""}$${amount}`;
}

function formatDate(value: string | null): string {
  if (!value) return "";
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.valueOf())) return value;
  return parsed.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function StatementHeader({ summary }: { summary: Summary }) {
  const targetNet = summary.totals.net;
  const [displayNet, setDisplayNet] = useState(targetNet);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (hasAnimated.current) {
      setDisplayNet(targetNet);
      return;
    }
    hasAnimated.current = true;
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion || typeof window.requestAnimationFrame !== "function") {
      setDisplayNet(targetNet);
      return;
    }

    const start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / 500);
      const eased = 1 - (1 - progress) ** 3;
      setDisplayNet(targetNet * eased);
      if (progress < 1) frame = window.requestAnimationFrame(tick);
    };
    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [targetNet]);

  const [from, to] = summary.range;
  const period = from && to ? `${formatDate(from)} — ${formatDate(to)}` : "All imported transactions";

  return (
    <div className="panel statement">
      <div className="statement__period">
        <p className="section-eyebrow">Statement period</p>
        <span className="statement__period-value">{period}</span>
      </div>
      <div className="statement__lines">
        <div className="statement__line">
          <span className="statement__label">Opening balance</span>
          <span className="statement__amount">$0.00</span>
        </div>
        <div className="statement__line">
          <span className="statement__label">Total in</span>
          <span className="statement__amount statement__amount--positive">{formatAmount(summary.totals.income, true)}</span>
        </div>
        <div className="statement__line">
          <span className="statement__label">Total out</span>
          <span className="statement__amount statement__amount--negative">{formatAmount(summary.totals.spend)}</span>
        </div>
        <div className="statement__line statement__net-line">
          <span className="statement__label">Net position</span>
          <span className="statement__net" aria-live="polite">{formatAmount(displayNet)}</span>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void Promise.all([getSummary(), listTransactions({ limit: 100, sort: "-date" }), getForecast()])
      .then(([nextSummary, nextTransactions, nextForecast]) => {
        setSummary(nextSummary);
        setTransactions(nextTransactions.transactions);
        setForecast(nextForecast);
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

  if (error) return <p role="alert" className="error-message">{error}</p>;
  if (!summary) return <p className="loading-message">Loading dashboard…</p>;

  return (
    <section className="page page--dashboard">
      <header className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-summary">Your spending at a glance.</p>
        </div>
      </header>
      <StatementHeader summary={summary} />
      <div className="dashboard-grid">
        <CategoryBarChart data={summary.by_category} />
        <MonthlyTrendChart data={summary.monthly} />
      </div>
      <section>
        <h2 className="section-eyebrow spacer-heading">Top merchants</h2>
        <div className="ledger-table-wrap">
          <table className="ledger-table">
            <thead>
              <tr><th>Merchant</th><th className="numeric">Amount</th><th className="numeric">Transactions</th></tr>
            </thead>
            <tbody>
              {summary.top_merchants.map((merchant) => (
                <tr key={merchant.merchant}>
                  <td>{merchant.merchant}</td>
                  <td className="numeric">{formatAmount(merchant.total)}</td>
                  <td className="numeric">{merchant.txn_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {forecast && <ForecastCard data={forecast} />}
      <section>
        <h2 className="section-eyebrow spacer-heading">Recent transactions</h2>
        <DataTable transactions={transactions} onCategoryChange={changeCategory} />
      </section>
    </section>
  );
}
