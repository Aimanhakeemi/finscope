import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MonthlyTotal } from "../api/client";

interface Props {
  data: MonthlyTotal[];
}

function formatCurrency(value: number, fractionDigits = 0): string {
  return `$${Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })}`;
}

export default function MonthlyTrendChart({ data }: Props) {
  const chartData = data.map((item) => ({
    month: item.month,
    spend: Math.abs(item.spend),
    income: item.income,
  }));

  return (
    <section className="panel chart-panel">
      <h2 className="section-eyebrow">Monthly trend</h2>
      <div className="chart-panel__plot">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ left: 8, right: 12 }}>
            <CartesianGrid stroke="var(--rule)" />
            <XAxis
              dataKey="month"
              tick={{ fill: "var(--ink-soft)" }}
              axisLine={{ stroke: "var(--rule)" }}
              tickLine={{ stroke: "var(--rule)" }}
            />
            <YAxis
              tickFormatter={(value) => formatCurrency(Number(value))}
              tick={{ fill: "var(--ink-soft)" }}
              axisLine={{ stroke: "var(--rule)" }}
              tickLine={{ stroke: "var(--rule)" }}
            />
            <Tooltip
              formatter={(value, name) => [formatCurrency(Number(value), 2), name]}
              contentStyle={{
                backgroundColor: "var(--paper)",
                border: "1px solid var(--rule)",
                borderRadius: "4px",
                color: "var(--ink)",
                fontFamily: "IBM Plex Mono, monospace",
                fontSize: "12px",
              }}
              labelStyle={{ color: "var(--ink-soft)" }}
              itemStyle={{ color: "var(--ink)" }}
            />
            <Legend
              align="right"
              verticalAlign="top"
              height={24}
              wrapperStyle={{ color: "var(--ink-soft)" }}
            />
            <Line type="monotone" dataKey="spend" name="Spend" stroke="var(--flag)" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="income" name="Income" stroke="var(--ledger)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
