import type { ForecastResponse } from "../api/client";
import { humanizeCategory } from "../format";

interface Props {
  data: ForecastResponse;
}

function formatSpend(value: number): string {
  const amount = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return value < 0 ? `− $${amount}` : `$${amount}`;
}

export default function ForecastCard({ data }: Props) {
  return (
    <section className="panel forecast-panel">
      <div className="forecast-panel__header">
        <div>
          <p className="section-eyebrow">Forecast</p>
          <h2 className="forecast-panel__title">Next-month forecast</h2>
          <p className="muted">{data.next_month} · {data.method.replace("_", " ")}</p>
        </div>
        <p className="forecast-panel__value">{formatSpend(data.total_spend.point)}</p>
      </div>
      <p className="forecast-panel__range">80% range: {formatSpend(data.total_spend.low)} to {formatSpend(data.total_spend.high)}</p>
      {data.by_category.length > 0 && (
        <div className="forecast-grid">
          {data.by_category.slice(0, 6).map((item) => (
            <div key={item.category} className="forecast-item">
              <p className="forecast-item__category">{humanizeCategory(item.category)}</p>
              <p className="forecast-item__value">{formatSpend(item.point)}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
