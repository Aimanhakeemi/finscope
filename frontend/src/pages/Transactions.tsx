import { useEffect, useState } from "react";
import DataTable from "../components/DataTable";
import { listTransactions, TAXONOMY, updateTransactionCategory, type Category, type TransactionsResponse } from "../api/client";
import { humanizeCategory } from "../format";

const PAGE_SIZE = 50;

interface Filters {
  category: Category | "";
  isRecurring: "" | "true" | "false";
  isAnomaly: "" | "true" | "false";
  from: string;
  to: string;
}

const INITIAL_FILTERS: Filters = {
  category: "",
  isRecurring: "",
  isAnomaly: "",
  from: "",
  to: "",
};

function asBoolean(value: "" | "true" | "false"): boolean | undefined {
  return value === "" ? undefined : value === "true";
}

export default function Transactions() {
  const [data, setData] = useState<TransactionsResponse | null>(null);
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [page, setPage] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null);
    setError("");
    void listTransactions({
      category: filters.category || undefined,
      from: filters.from || undefined,
      to: filters.to || undefined,
      is_recurring: asBoolean(filters.isRecurring),
      is_anomaly: asBoolean(filters.isAnomaly),
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      sort: "-date",
    })
      .then(setData)
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Could not load transactions."));
  }, [filters, page]);

  function updateFilter<Key extends keyof Filters>(key: Key, value: Filters[Key]) {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(0);
  }

  async function changeCategory(id: string, category: Category) {
    try {
      const updated = await updateTransactionCategory(id, category);
      setData((current) => current ? {
        ...current,
        transactions: current.transactions.map((item) => item.id === id ? updated : item),
      } : current);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update category.");
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const firstRow = data && data.total > 0 ? page * PAGE_SIZE + 1 : 0;
  const lastRow = data ? Math.min((page + 1) * PAGE_SIZE, data.total) : 0;

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1 className="page-title">Transactions</h1>
          <p className="page-summary">Review, filter, and correct the transactions in your statement.</p>
        </div>
      </header>
      <section className="panel transaction-filters">
        <h2 className="section-eyebrow">Filter transactions</h2>
        <div className="transaction-filters__grid">
          <label>
            <span className="field-label">Category</span>
            <select aria-label="Category" className="field" value={filters.category} onChange={(event) => updateFilter("category", event.target.value as Filters["category"])}>
              <option value="">All categories</option>
              {TAXONOMY.map((category) => <option key={category} value={category}>{humanizeCategory(category)}</option>)}
            </select>
          </label>
          <label>
            <span className="field-label">Recurring</span>
            <select aria-label="Recurring" className="field" value={filters.isRecurring} onChange={(event) => updateFilter("isRecurring", event.target.value as Filters["isRecurring"])}>
              <option value="">All transactions</option>
              <option value="true">Recurring only</option>
              <option value="false">Non-recurring only</option>
            </select>
          </label>
          <label>
            <span className="field-label">Anomaly</span>
            <select aria-label="Anomaly" className="field" value={filters.isAnomaly} onChange={(event) => updateFilter("isAnomaly", event.target.value as Filters["isAnomaly"])}>
              <option value="">All transactions</option>
              <option value="true">Anomalies only</option>
              <option value="false">Non-anomalies only</option>
            </select>
          </label>
          <label>
            <span className="field-label">From date</span>
            <input aria-label="From date" className="field" type="date" value={filters.from} onChange={(event) => updateFilter("from", event.target.value)} />
          </label>
          <label>
            <span className="field-label">To date</span>
            <input aria-label="To date" className="field" type="date" value={filters.to} onChange={(event) => updateFilter("to", event.target.value)} />
          </label>
        </div>
      </section>
      {error ? (
        <p role="alert" className="error-message">{error}</p>
      ) : data ? (
        <section>
          <div className="table-section__header">
            <h2 className="section-eyebrow spacer-heading">Transactions</h2>
            <span className="caption">{firstRow}–{lastRow} of {data.total}</span>
          </div>
          {data.transactions.length > 0 ? (
            <DataTable transactions={data.transactions} onCategoryChange={changeCategory} />
          ) : (
            <p className="panel empty-state">No transactions match these filters.</p>
          )}
        </section>
      ) : (
        <p className="loading-message">Loading transactions…</p>
      )}
      {data && data.total > 0 && (
        <nav className="pagination" aria-label="Transaction pagination">
          <p className="pagination__summary">Page {page + 1} of {totalPages}</p>
          <div className="form-actions">
            <button type="button" className="button button--secondary" disabled={page === 0} onClick={() => setPage((current) => current - 1)}>
              Previous
            </button>
            <button type="button" className="button button--secondary" disabled={page + 1 >= totalPages} onClick={() => setPage((current) => current + 1)}>
              Next
            </button>
          </div>
        </nav>
      )}
    </section>
  );
}
