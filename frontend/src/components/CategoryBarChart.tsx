import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CategoryTotal } from "../api/client";

interface Props {
  data: CategoryTotal[];
}

const formatDollars = (value: number) => `$${Number(value).toLocaleString()}`;

export default function CategoryBarChart({ data }: Props) {
  // "Spend by category" — income is not spend.
  const chartData = data
    .filter((item) => item.category !== "income")
    .map((item) => ({
      category: item.category.replace(/_/g, " "),
      spent: Math.abs(item.total),
    }))
    .sort((a, b) => b.spent - a.spent);

  return (
    <div className="h-80 rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-4 text-lg font-medium">Spend by category</h2>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={chartData} layout="vertical" margin={{ left: 24, right: 16 }}>
          <CartesianGrid stroke="#1e293b" horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={formatDollars}
            stroke="#94a3b8"
          />
          <YAxis
            dataKey="category"
            type="category"
            width={150}
            interval={0}
            tickLine={false}
            stroke="#94a3b8"
          />
          <Tooltip
            formatter={(value) => [
              `$${Number(value).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`,
              "spend",
            ]}
          />
          <Bar dataKey="spent" fill="#38bdf8" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
