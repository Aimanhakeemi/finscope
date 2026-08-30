import { useEffect, useState } from "react";
import { listAlerts, type AlertsResponse } from "../api/client";
import { formatDate, humanizeCategory, humanizeSignal } from "../format";

function formatAmount(value: number): string {
  const amount = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return value < 0 ? `− $${amount}` : `$${amount}`;
}

export default function Alerts() {
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void listAlerts()
      .then(setData)
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Could not load alerts."));
  }, []);

  if (error) return <p role="alert" className="error-message">{error}</p>;
  if (!data) return <p className="loading-message">Loading alerts…</p>;

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1 className="page-title">Alerts</h1>
          <p className="page-summary">Unusual non-recurring charges from the latest period.</p>
        </div>
      </header>
      {data.alerts.length === 0 ? (
        <p className="panel empty-state">No unusual charges in this period.</p>
      ) : (
        <div className="ledger-table-wrap">
          <table className="ledger-table ledger-table--alerts">
            <thead>
              <tr><th>Merchant</th><th>Date</th><th className="numeric">Amount</th><th>Signals</th></tr>
            </thead>
            <tbody>
              {data.alerts.map((alert) => (
                <tr key={alert.transaction_id}>
                  <td>
                    {alert.description_raw}
                    <span className="subline">{alert.reason}</span>
                  </td>
                  <td className="date-cell">
                    {formatDate(alert.txn_date)}
                    <span className="subline">{humanizeCategory(alert.category)}</span>
                  </td>
                  <td className="numeric flag-amount">{formatAmount(alert.amount)}</td>
                  <td>
                    {alert.signals.map((signal) => <span key={signal} className="flag-tag">{humanizeSignal(signal)}</span>)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
