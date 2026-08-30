import { FormEvent, useState } from "react";
import { askQuestion, type AskResponse } from "../api/client";

const DISABLED_NOTE = "Natural-language questions need an API key. Add `ANTHROPIC_API_KEY` to your `.env` to enable this.";

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

  const disabled = error.includes("ANTHROPIC_API_KEY");
  const singleValue = answer && answer.rows.length === 1 && answer.columns.length === 1;

  return (
    <section className="page page--narrow">
      <header className="page-header">
        <div>
          <h1 className="page-title">Ask FinScope</h1>
          <p className="page-summary">Ask a question about your imported spending.</p>
        </div>
      </header>
      <form onSubmit={submit} className="panel ask-form">
        <div className="ask-form__row">
          <input
            aria-label="Spending question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="e.g. how much did I spend on coffee since June?"
            className="field"
          />
          <button type="submit" disabled={busy} className="button button--primary">
            {busy ? "Asking…" : "Ask"}
          </button>
        </div>
      </form>
      {disabled && <p className="panel disabled-note">{DISABLED_NOTE}</p>}
      {error && !disabled && <p role="alert" className="error-message">{error}</p>}
      {answer && (
        <div className="ask-result">
          <section className={`statement-answer${singleValue ? " statement-answer--aggregate" : ""}`}>
            <p className="section-eyebrow">Answer</p>
            {answer.rows.length === 0 ? (
              <p className="empty-state">No matching rows.</p>
            ) : singleValue ? (
              <p className="statement-answer__value">{displayValue(answer.rows[0][answer.columns[0]])}</p>
            ) : (
              <div className="ledger-table-wrap">
                <table className="ledger-table">
                  <thead><tr>{answer.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
                  <tbody>{answer.rows.map((row, index) => <tr key={index}>{answer.columns.map((column) => <td key={column} className={typeof row[column] === "number" ? "numeric" : ""}>{displayValue(row[column])}</td>)}</tr>)}</tbody>
                </table>
              </div>
            )}
            {answer.truncated && <p className="caption">Results capped at 500 rows.</p>}
          </section>
          <section className="query-panel">
            <p className="section-eyebrow">Query</p>
            <pre aria-label="Generated SQL"><code>{answer.sql}</code></pre>
            <p className="caption query-panel__caption">Read-only query against the protected transaction view.</p>
          </section>
        </div>
      )}
    </section>
  );
}
