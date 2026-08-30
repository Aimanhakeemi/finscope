import { useEffect, useState } from "react";
import { listSubscriptions, type SubscriptionsResponse } from "../api/client";

function formatCurrency(value: number): string {
  return `$${Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export default function Subscriptions() {
  const [data, setData] = useState<SubscriptionsResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void listSubscriptions()
      .then(setData)
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Could not load subscriptions."));
  }, []);

  if (error) return <p role="alert" className="error-message">{error}</p>;
  if (!data) return <p className="loading-message">Loading subscriptions…</p>;

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1 className="page-title">Subscriptions</h1>
          <p className="page-summary">Recurring charges found in your statement.</p>
        </div>
      </header>
      <div className="summary-pair">
        <div>
          <p className="section-eyebrow">Estimated monthly cost</p>
          <p className="summary-pair__value">{formatCurrency(data.total_monthly_cost)}</p>
        </div>
        <div>
          <p className="section-eyebrow">Estimated annual cost</p>
          <p className="summary-pair__value">{formatCurrency(data.total_annual_cost)}</p>
        </div>
      </div>
      {data.subscriptions.length === 0 ? (
        <p className="panel empty-state">No recurring charges found yet.</p>
      ) : (
        <div className="ledger-table-wrap">
          <table className="ledger-table">
            <thead>
              <tr>
                <th>Merchant</th>
                <th>Cadence</th>
                <th className="numeric">Monthly cost</th>
                <th>Next expected</th>
                <th aria-label="Status" />
              </tr>
            </thead>
            <tbody>
              {data.subscriptions.map((subscription) => (
                <tr key={subscription.recurring_group_id} className={subscription.active ? "" : "row--inactive"}>
                  <td>
                    {subscription.merchant}
                    <span className="subline">{subscription.occurrences} occurrences</span>
                    {subscription.price_changed && (
                      <>
                        <span className="flag-tag">price up</span>
                        <span className="visually-hidden">Price changed by more than 5%.</span>
                      </>
                    )}
                  </td>
                  <td>{subscription.cadence}</td>
                  <td className="numeric">{formatCurrency(subscription.monthly_cost)}</td>
                  <td>{subscription.next_expected}</td>
                  <td>
                    <span className={`status-dot${subscription.active ? "" : " status-dot--inactive"}`} aria-hidden="true" />
                    <span className="visually-hidden">{subscription.active ? "Active" : "Inactive"}</span>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="ledger-table__total">
                <td colSpan={2}>Total</td>
                <td colSpan={3} className="numeric">{formatCurrency(data.total_monthly_cost)} / month · {formatCurrency(data.total_annual_cost)} / year</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </section>
  );
}
