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

export default function MonthlyTrendChart({ data }: Props) {
  // Plot both series as positive magnitudes so income and spend are directly
  // comparable and the y-axis never shows a mislabelled negative tick.
  const chartData = data.map((d) => ({
    month: d.month,
    Income: d.income,
    Spend: Math.abs(d.spend),
  }));

  return (
    <div className="h-80 rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-4 text-lg font-medium">Monthly trend</h2>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={chartData} margin={{ left: 8, right: 12 }}>
          <CartesianGrid stroke="#1e293b" />
          <XAxis dataKey="month" stroke="#94a3b8" />
          <YAxis
            tickFormatter={(value) => `$${Number(value).toLocaleString()}`}
            stroke="#94a3b8"
          />
          <Tooltip
            formatter={(value, name) => [
              `$${Number(value).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`,
              name,
            ]}
          />
          <Legend />
          <Line type="monotone" dataKey="Income" stroke="#4ade80" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Spend" stroke="#f472b6" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
