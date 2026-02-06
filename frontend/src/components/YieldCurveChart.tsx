import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { YieldPoint } from "../api/yields";

interface YieldCurveChartProps {
  data: YieldPoint[];
}

export function YieldCurveChart({ data }: YieldCurveChartProps) {
  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart
        data={data}
        margin={{ top: 16, right: 24, left: 8, bottom: 8 }}
      >
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200" />
        <XAxis
          dataKey="term"
          tick={{ fontSize: 12, fill: "#374151" }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
        />
        <YAxis
          dataKey="rate"
          tick={{ fontSize: 12, fill: "#374151" }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
          tickFormatter={(v) => `${v}%`}
          domain={["auto", "auto"]}
        />
        <Tooltip
          formatter={(value: number) => [`${value}%`, "Yield"]}
          labelFormatter={(label) => `Term: ${label}`}
          contentStyle={{
            borderRadius: "8px",
            border: "1px solid #e5e7eb",
            fontSize: "13px",
          }}
        />
        <Line
          type="monotone"
          dataKey="rate"
          stroke="#0f766e"
          strokeWidth={2}
          dot={{ fill: "#0f766e", strokeWidth: 0, r: 4 }}
          activeDot={{ r: 6, fill: "#0d9488" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
