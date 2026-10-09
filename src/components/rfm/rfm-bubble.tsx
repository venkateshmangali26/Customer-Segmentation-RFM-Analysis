"use client";

import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CustomerRfm, SegmentSummary } from "./types";
import { formatInr } from "@/lib/format";

type Props = {
  customers: CustomerRfm[];
  segments: SegmentSummary[];
};

export function RfmBubbleChart({ customers, segments }: Props) {
  // One scatter series per segment for color coding
  const segmentColorMap = new Map(segments.map((s) => [s.segment, s.color]));

  // Group customers by segment
  const bySegment = new Map<string, CustomerRfm[]>();
  for (const c of customers) {
    const arr = bySegment.get(c.segment) ?? [];
    arr.push(c);
    bySegment.set(c.segment, arr);
  }

  const series = Array.from(bySegment.entries()).map(([segment, custs]) => ({
    segment,
    color: segmentColorMap.get(segment) ?? "#9ca3af",
    data: custs.map((c) => ({
      x: c.recencyDays,
      y: c.frequency,
      z: c.monetary,
      name: c.customerName,
      rfmScore: c.rfmScore,
      monetary: c.monetary,
      segment,
    })),
  }));

  return (
    <Card className="border-border/60">
      <CardHeader>
        <CardTitle className="text-base">Customer Map — Recency × Frequency × Monetary</CardTitle>
        <CardDescription>
          Each dot is a customer. X = days since last purchase, Y = order count, bubble size = total spend.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[360px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                type="number"
                dataKey="x"
                name="Recency"
                unit="d"
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                label={{
                  value: "Recency (days since last purchase)",
                  position: "insideBottom",
                  offset: -15,
                  fill: "var(--muted-foreground)",
                  fontSize: 11,
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Frequency"
                allowDecimals={false}
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                label={{
                  value: "Frequency (orders)",
                  angle: -90,
                  position: "insideLeft",
                  offset: 10,
                  fill: "var(--muted-foreground)",
                  fontSize: 11,
                }}
              />
              <ZAxis
                type="number"
                dataKey="z"
                range={[60, 800]}
                name="Monetary"
              />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                content={({ active, payload }) => {
                  if (!active || !payload || payload.length === 0) return null;
                  const d = payload[0].payload as {
                    name: string;
                    x: number;
                    y: number;
                    monetary: number;
                    rfmScore: string;
                    segment: string;
                  };
                  return (
                    <div className="rounded-lg border border-border bg-popover p-3 text-popover-foreground shadow-md max-w-xs">
                      <div className="font-medium text-sm">{d.name}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Recency: <span className="font-medium text-foreground">{d.x} days</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Frequency: <span className="font-medium text-foreground">{d.y} orders</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Monetary: <span className="font-medium text-foreground">{formatInr(d.monetary, false)}</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        RFM score: <span className="font-mono text-foreground">{d.rfmScore}</span>
                      </div>
                    </div>
                  );
                }}
              />
              {series.map((s) => (
                <Scatter
                  key={s.segment}
                  name={s.segment}
                  data={s.data}
                  fill={s.color}
                  fillOpacity={0.75}
                />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        {/* Custom legend below chart — wraps on small screens */}
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-3 px-2">
          {series.map((s) => (
            <div key={s.segment} className="flex items-center gap-1.5">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span className="text-xs text-muted-foreground">{s.segment}</span>
              <span className="text-xs text-muted-foreground/60 tabular-nums">
                ({s.data.length})
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
