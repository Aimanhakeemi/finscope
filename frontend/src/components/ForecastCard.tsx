import type { ForecastResponse } from "../api/client";

interface Props {
  data: ForecastResponse;
}

function formatSpend(value: number): string {
  const amount = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return value < 0 ? `-$${amount}` : `$${amount}`;
}

export default function ForecastCard({ data }: Props) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-medium">Next-month forecast</h2>
          <p className="mt-1 text-sm text-slate-400">{data.next_month} · {data.method.replace("_", " ")}</p>
        </div>
        <p className="text-xl font-semibold">{formatSpend(data.total_spend.point)}</p>
      </div>
      <p className="mt-2 text-sm text-slate-400">80% range: {formatSpend(data.total_spend.low)} to {formatSpend(data.total_spend.high)}</p>
      {data.by_category.length > 0 && (
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.by_category.slice(0, 6).map((item) => (
            <div key={item.category} className="rounded bg-slate-950 p-3">
              <p className="capitalize text-sm text-slate-400">{item.category.replace(/_/g, " ")}</p>
              <p className="mt-1 font-medium">{formatSpend(item.point)}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
