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
    <section className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Import statement</h1>
        <p className="mt-2 text-slate-400">Upload a CSV with date, description, and amount columns.</p>
      </div>
      <form onSubmit={submit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
        <label className="block">
          <span className="mb-2 block text-sm text-slate-300">Statement CSV</span>
          <input
            aria-label="Statement CSV"
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="block w-full text-sm text-slate-300"
          />
        </label>
        <div className="grid gap-4 md:grid-cols-6">
          <label>
            <span className="mb-1 block text-xs text-slate-400">Date format</span>
            <select value={dateFormat} onChange={(event) => setDateFormat(event.target.value)} className="field">
              <option value="YMD">YYYY-MM-DD</option>
              <option value="MDY">MM/DD/YYYY</option>
              <option value="DMY">DD/MM/YYYY</option>
            </select>
          </label>
          <input aria-label="Date column" placeholder="Date column" value={dateColumn} onChange={(event) => setDateColumn(event.target.value)} className="field" />
          <input aria-label="Description column" placeholder="Description column" value={descriptionColumn} onChange={(event) => setDescriptionColumn(event.target.value)} className="field" />
          <input aria-label="Amount column" placeholder="Amount column" value={amountColumn} onChange={(event) => setAmountColumn(event.target.value)} className="field" />
          <input aria-label="Debit column" placeholder="Debit column" value={debitColumn} onChange={(event) => setDebitColumn(event.target.value)} className="field" />
          <input aria-label="Credit column" placeholder="Credit column" value={creditColumn} onChange={(event) => setCreditColumn(event.target.value)} className="field" />
        </div>
        <button disabled={busy} className="rounded bg-sky-500 px-4 py-2 font-medium text-slate-950 disabled:opacity-50">
          {busy ? "Importing…" : "Import CSV"}
        </button>
        <p className="text-xs text-slate-500">Only transaction descriptions and amounts are processed; FinScope is not financial advice.</p>
        {error && <p role="alert" className="text-sm text-rose-400">{error}</p>}
      </form>
      {result && (
        <div className="rounded-xl border border-emerald-900 bg-emerald-950/30 p-6">
          <h2 className="text-xl font-medium">{result.filename} imported</h2>
          <p className="mt-2 text-slate-300">Rows accepted: {result.rows_accepted} · Deduped: {result.rows_deduped}</p>
          <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(result.category_breakdown).map(([category, count]) => (
              <div key={category} className="flex justify-between rounded bg-slate-900 px-3 py-2 text-sm">
                <span>{category}</span><span>{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
