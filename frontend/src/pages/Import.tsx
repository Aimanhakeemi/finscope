import { FormEvent, useState } from "react";
import { uploadImport, type ImportSummary } from "../api/client";

export default function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dateFormat, setDateFormat] = useState("YMD");
  const [dateColumn, setDateColumn] = useState("");
  const [descriptionColumn, setDescriptionColumn] = useState("");
  const [amountColumn, setAmountColumn] = useState("");
  const [debitColumn, setDebitColumn] = useState("");
  const [creditColumn, setCreditColumn] = useState("");
  const [result, setResult] = useState<ImportSummary | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const mapping: Record<string, string> = {};
      if (dateColumn) mapping.date = dateColumn;
      if (descriptionColumn) mapping.description = descriptionColumn;
      if (amountColumn) mapping.amount = amountColumn;
      if (debitColumn) mapping.debit = debitColumn;
      if (creditColumn) mapping.credit = creditColumn;
      if (dateFormat !== "YMD") mapping.date_format = dateFormat;
      setResult(await uploadImport(file, mapping));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Import failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="page page--narrow">
      <header className="page-header">
        <div>
          <h1 className="page-title">Import statement</h1>
          <p className="page-summary">Upload a CSV with date, description, and amount columns.</p>
        </div>
      </header>
      <form onSubmit={submit} className="panel form-panel">
        <label>
          <span className="field-label field-label--file">Statement CSV</span>
          <input
            aria-label="Statement CSV"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="field field--file"
          />
        </label>
        <div className="form-grid">
          <label>
            <span className="field-label">Date format</span>
            <select value={dateFormat} onChange={(event) => setDateFormat(event.target.value)} className="field">
              <option value="YMD">YYYY-MM-DD</option>
              <option value="MDY">MM/DD/YYYY</option>
              <option value="DMY">DD/MM/YYYY</option>
            </select>
          </label>
          <label>
            <span className="field-label">Date column</span>
            <input aria-label="Date column" placeholder="Date column" value={dateColumn} onChange={(event) => setDateColumn(event.target.value)} className="field" />
          </label>
          <label>
            <span className="field-label">Description column</span>
            <input aria-label="Description column" placeholder="Description column" value={descriptionColumn} onChange={(event) => setDescriptionColumn(event.target.value)} className="field" />
          </label>
          <label>
            <span className="field-label">Amount column</span>
            <input aria-label="Amount column" placeholder="Amount column" value={amountColumn} onChange={(event) => setAmountColumn(event.target.value)} className="field" />
          </label>
          <label>
            <span className="field-label">Debit column</span>
            <input aria-label="Debit column" placeholder="Debit column" value={debitColumn} onChange={(event) => setDebitColumn(event.target.value)} className="field" />
          </label>
          <label>
            <span className="field-label">Credit column</span>
            <input aria-label="Credit column" placeholder="Credit column" value={creditColumn} onChange={(event) => setCreditColumn(event.target.value)} className="field" />
          </label>
        </div>
        <div className="form-actions">
          <button type="submit" disabled={busy} className="button button--primary">
            {busy ? "Importing…" : "Import CSV"}
          </button>
        </div>
        <p className="caption">Only transaction descriptions and amounts are processed; FinScope is not financial advice.</p>
        {error && <p role="alert" className="error-message">{error}</p>}
      </form>
      {result && (
        <div className="panel result-panel">
          <h2 className="result-panel__title">{result.filename} imported</h2>
          <p className="result-panel__summary">Rows accepted: {result.rows_accepted} · Deduped: {result.rows_deduped}</p>
          <div className="breakdown-grid">
            {Object.entries(result.category_breakdown).map(([category, count]) => (
              <div key={category} className="breakdown-item">
                <span>{category}</span><span className="data-number">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
