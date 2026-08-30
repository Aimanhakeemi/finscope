import { FormEvent, useState } from "react";
import { askQuestion, type AskResponse } from "../api/client";

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  return String(value);
}

export default function Ask() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) {
      setError("Ask a question about your spending.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      setAnswer(await askQuestion(question.trim()));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ask failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Ask FinScope</h1>
        <p className="mt-2 text-slate-400">Ask a question about your imported spending.</p>
      </div>
      <form onSubmit={submit} className="flex gap-3 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <input
          aria-label="Spending question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="How much did I spend on coffee since June?"
          className="field flex-1"
        />
        <button disabled={busy} className="rounded bg-sky-500 px-4 py-2 font-medium text-slate-950 disabled:opacity-50">
          {busy ? "Asking…" : "Ask"}
        </button>
      </form>
      {error && <p role="alert" className="text-rose-400">{error}</p>}
      {answer && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h2 className="mb-3 text-lg font-medium">Answer</h2>
            {answer.rows.length === 0 ? (
              <p className="text-slate-400">No matching rows.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead><tr>{answer.columns.map((column) => <th key={column} className="border-b border-slate-800 px-3 py-2 text-slate-400">{column}</th>)}</tr></thead>
                  <tbody>{answer.rows.map((row, index) => <tr key={index}>{answer.columns.map((column) => <td key={column} className="border-b border-slate-800 px-3 py-2">{displayValue(row[column])}</td>)}</tr>)}</tbody>
                </table>
              </div>
            )}
            {answer.truncated && <p className="mt-3 text-xs text-amber-300">Results capped at 500 rows.</p>}
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
            <h2 className="mb-3 text-lg font-medium">Generated SQL</h2>
            <pre aria-label="Generated SQL" className="overflow-x-auto rounded bg-slate-950 p-4 text-sm text-slate-300"><code>{answer.sql}</code></pre>
            <p className="mt-3 text-xs text-slate-500">Read-only query against the protected transaction view.</p>
          </div>
        </div>
      )}
    </section>
  );
}
