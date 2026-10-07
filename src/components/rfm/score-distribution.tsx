"use client";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ScoreDistribution } from "./types";

type Props = {
  distribution: ScoreDistribution;
};

export function ScoreDistributionChart({ distribution }: Props) {
  // Build data for grouped bars (R, F, M for scores 1..5)
  const data = [1, 2, 3, 4, 5].map((score, i) => ({
    score: `${score}`,
    Recency: distribution.r[i],
    Frequency: distribution.f[i],
    Monetary: distribution.m[i],
  }));

  return (
    <Card className="border-border/60">
      <CardHeader>
        <CardTitle className="text-base">R / F / M Score Distribution</CardTitle>
        <CardDescription>
          Number of customers at each quantile score (1=low, 5=high)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barGap={4} barCategoryGap="20%">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="score"
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                label={{
                  value: "Score",
                  position: "insideBottom",
                  offset: -2,
                  fill: "var(--muted-foreground)",
                  fontSize: 12,
                }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                allowDecimals={false}
              />
              <Tooltip
                cursor={{ fill: "var(--accent)", opacity: 0.3 }}
                content={({ active, payload, label }) => {
                  if (!active || !payload || payload.length === 0) return null;
                  return (
                    <div className="rounded-lg border border-border bg-popover p-3 text-popover-foreground shadow-md">
                      <div className="text-xs font-medium mb-1">Score {label}</div>
                      {payload.map((p) => (
                        <div
                          key={p.dataKey as string}
                          className="flex items-center gap-2 text-xs"
                        >
                          <span
                            className="h-2 w-2 rounded-full"
                            style={{ backgroundColor: p.color }}
                          />
                          <span className="text-muted-foreground">{p.dataKey as string}:</span>
                          <span className="font-medium tabular-nums">{p.value}</span>
                        </div>
                      ))}
                    </div>
                  );
                }}
              />
              <Legend
                iconType="circle"
                iconSize={8}
                formatter={(value) => (
                  <span className="text-xs text-muted-foreground">{value}</span>
                )}
              />
              <Bar dataKey="Recency" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Frequency" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Monetary" fill="#a855f7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
