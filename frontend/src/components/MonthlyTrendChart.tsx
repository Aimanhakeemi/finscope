import {
  CartesianGrid,
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
  return (
    <div className="h-80 rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-4 text-lg font-medium">Monthly trend</h2>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data} margin={{ left: 8, right: 12 }}>
          <CartesianGrid stroke="#1e293b" />
          <XAxis dataKey="month" stroke="#94a3b8" />
          <YAxis tickFormatter={(value) => `$${Math.abs(value)}`} stroke="#94a3b8" />
          <Tooltip formatter={(value) => [`$${Math.abs(Number(value)).toFixed(2)}`, ""]} />
          <Line type="monotone" dataKey="spend" name="spend" stroke="#f472b6" strokeWidth={2} />
          <Line type="monotone" dataKey="income" name="income" stroke="#4ade80" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
