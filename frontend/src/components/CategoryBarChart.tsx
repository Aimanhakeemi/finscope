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

export default function CategoryBarChart({ data }: Props) {
  const chartData = data.map((item) => ({ ...item, spent: Math.abs(item.total) }));
  return (
    <div className="h-80 rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-4 text-lg font-medium">Spend by category</h2>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 12 }}>
          <CartesianGrid stroke="#1e293b" horizontal={false} />
          <XAxis type="number" tickFormatter={(value) => `$${value}`} stroke="#94a3b8" />
          <YAxis dataKey="category" type="category" width={110} stroke="#94a3b8" />
          <Tooltip formatter={(value) => [`$${Number(value).toFixed(2)}`, "spend"]} />
          <Bar dataKey="spent" fill="#38bdf8" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
