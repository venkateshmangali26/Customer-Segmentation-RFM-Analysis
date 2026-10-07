"use client";

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { SegmentSummary } from "./types";

type Props = {
  segments: SegmentSummary[];
};

function formatMoney(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

export function SegmentDonut({ segments }: Props) {
  const totalCustomers = segments.reduce((s, x) => s + x.count, 0);
  const data = segments.map((s) => ({
    name: s.segment,
    value: s.count,
    color: s.color,
    revenue: s.revenue,
    pct: totalCustomers > 0 ? (s.count / totalCustomers) * 100 : 0,
  }));

  return (
    <Card className="border-border/60">
      <CardHeader>
        <CardTitle className="text-base">Customer Segment Distribution</CardTitle>
        <CardDescription>
          Share of customers in each RFM segment
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={2}
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload || payload.length === 0) return null;
                  const d = payload[0].payload as (typeof data)[0];
                  return (
                    <div className="rounded-lg border border-border bg-popover p-3 text-popover-foreground shadow-md">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: d.color }}
                        />
                        <span className="font-medium">{d.name}</span>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {d.value} customers · {d.pct.toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Revenue: {formatMoney(d.revenue)}
                      </div>
                    </div>
                  );
                }}
              />
              <Legend
                layout="vertical"
                align="right"
                verticalAlign="middle"
                iconType="circle"
                iconSize={8}
                formatter={(value) => (
                  <span className="text-xs text-muted-foreground">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
