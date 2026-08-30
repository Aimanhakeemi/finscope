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
import { humanizeCategory } from "../format";

interface Props {
  data: CategoryTotal[];
}

function formatCurrency(value: number): string {
  return `$${Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}

function formatTooltip(value: number): string {
  return `$${Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export default function CategoryBarChart({ data }: Props) {
  const chartData = data
    .filter((item) => item.category !== "income")
    .map((item) => ({
      category: humanizeCategory(item.category),
      spent: Math.abs(item.total),
    }))
    .sort((a, b) => b.spent - a.spent);

  return (
    <section className="panel chart-panel">
      <h2 className="section-eyebrow">Spend by category</h2>
      <div className="chart-panel__plot">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 4, right: 16 }}>
            <CartesianGrid stroke="var(--rule)" horizontal={false} />
            <XAxis
              type="number"
              tickFormatter={formatCurrency}
              tick={{ fill: "var(--ink-soft)" }}
              axisLine={{ stroke: "var(--rule)" }}
              tickLine={{ stroke: "var(--rule)" }}
            />
            <YAxis
              dataKey="category"
              type="category"
              width={150}
              interval={0}
              tickLine={false}
              axisLine={{ stroke: "var(--rule)" }}
              tick={{ fill: "var(--ink-soft)" }}
            />
            <Tooltip
              formatter={(value) => [formatTooltip(Number(value)), "Spend"]}
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
            <Bar dataKey="spent" name="Spend" fill="var(--flag)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
