import { useEffect, useState } from "react";
import { listAlerts, type AlertsResponse } from "../api/client";

export default function Alerts() {
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void listAlerts()
      .then(setData)
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Could not load alerts."));
  }, []);

  if (error) return <p role="alert" className="text-rose-400">{error}</p>;
  if (!data) return <p className="text-slate-400">Loading alerts…</p>;

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Alerts</h1>
        <p className="mt-2 text-slate-400">Unusual non-recurring charges from the latest period.</p>
      </div>
      {data.alerts.length === 0 ? (
        <p className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-slate-400">No alerts found.</p>
      ) : (
        <div className="space-y-4">
          {data.alerts.map((alert) => (
            <article key={alert.transaction_id} className="rounded-xl border border-rose-900/60 bg-slate-900 p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-medium">{alert.description_raw}</h2>
                  <p className="mt-1 text-sm text-slate-400">{alert.txn_date} · {alert.category}</p>
                </div>
                <p className="text-lg font-semibold text-rose-300">${Math.abs(alert.amount).toFixed(2)}</p>
              </div>
              <p className="mt-4 text-sm text-slate-300">{alert.reason}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {alert.signals.map((signal) => <span key={signal} className="rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-300">{signal}</span>)}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
