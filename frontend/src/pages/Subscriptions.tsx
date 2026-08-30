import { useEffect, useState } from "react";
import { listSubscriptions, type SubscriptionsResponse } from "../api/client";

export default function Subscriptions() {
  const [data, setData] = useState<SubscriptionsResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void listSubscriptions()
      .then(setData)
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Could not load subscriptions."));
  }, []);

  if (error) return <p role="alert" className="text-rose-400">{error}</p>;
  if (!data) return <p className="text-slate-400">Loading subscriptions…</p>;

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Subscriptions</h1>
        <p className="mt-2 text-slate-400">Recurring charges found in your statement.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">Estimated monthly cost</p>
          <p className="mt-2 text-2xl font-semibold">${data.total_monthly_cost.toFixed(2)}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">Estimated annual cost</p>
          <p className="mt-2 text-2xl font-semibold">${data.total_annual_cost.toFixed(2)}</p>
        </div>
      </div>
      {data.subscriptions.length === 0 ? (
        <p className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-slate-400">
          No recurring charges found yet.
        </p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.subscriptions.map((subscription) => (
            <article key={subscription.recurring_group_id} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-medium">{subscription.merchant}</h2>
                  <p className="mt-1 text-sm capitalize text-slate-400">
                    {subscription.cadence} · {subscription.occurrences} occurrences
                  </p>
                </div>
                <p className="text-lg font-semibold">${subscription.monthly_cost.toFixed(2)}/mo</p>
              </div>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div><dt className="text-slate-500">Average charge</dt><dd>${Math.abs(subscription.avg_amount).toFixed(2)}</dd></div>
                <div><dt className="text-slate-500">Next expected</dt><dd>{subscription.next_expected}</dd></div>
                <div><dt className="text-slate-500">Last seen</dt><dd>{subscription.last_seen}</dd></div>
                <div><dt className="text-slate-500">Status</dt><dd>{subscription.active ? "Active" : "Inactive"}</dd></div>
              </dl>
              {subscription.price_changed && <p className="mt-4 text-sm text-amber-300">Price changed by more than 5%.</p>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
