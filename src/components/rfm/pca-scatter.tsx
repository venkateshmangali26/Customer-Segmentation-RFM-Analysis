"use client";

import { useMemo, useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ZAxis,
  Cell,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Info, Filter } from "lucide-react";
import type { CustomerRfm, SegmentSummary } from "./types";
import { formatInr } from "@/lib/format";

type Props = {
  customers: CustomerRfm[];
  segments: SegmentSummary[];
  varianceExplained?: [number, number];
};

type ScatterDataPoint = {
  x: number;
  y: number;
  z: number;
  customerId: string;
  customerName: string;
  email: string;
  country: string;
  channel: string;
  segment: string;
  color: string;
  recencyDays: number;
  frequency: number;
  monetary: number;
  rfmScore: string;
  churnStatus: string;
  churnScore: number;
};

export function PcaClusterScatter({
  customers,
  segments,
  varianceExplained = [70, 20],
}: Props) {
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);

  const segmentColorMap = useMemo(
    () => new Map(segments.map((s) => [s.segment, s.color])),
    [segments]
  );

  const scatterData: ScatterDataPoint[] = useMemo(() => {
    return customers.map((c) => ({
      x: c.pc1 ?? 0,
      y: c.pc2 ?? 0,
      z: Math.max(40, Math.min(200, c.frequency * 12)),
      customerId: c.customerId,
      customerName: c.customerName,
      email: c.email,
      country: c.country,
      channel: c.channel,
      segment: c.segment,
      color: segmentColorMap.get(c.segment) ?? "#64748b",
      recencyDays: c.recencyDays,
      frequency: c.frequency,
      monetary: c.monetary,
      rfmScore: c.rfmScore,
      churnStatus: c.churnStatus ?? "Active",
      churnScore: c.churnScore ?? 0,
    }));
  }, [customers, segmentColorMap]);

  const displayedData = useMemo(() => {
    if (!selectedSegment) return scatterData;
    return scatterData.filter((d) => d.segment === selectedSegment);
  }, [scatterData, selectedSegment]);

  return (
    <Card className="border-border/60 shadow-sm overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                2D PCA Customer Cluster Space
              </CardTitle>
              <Badge variant="outline" className="text-xs font-normal">
                PC1 ({varianceExplained[0]}%) · PC2 ({varianceExplained[1]}%)
              </Badge>
            </div>
            <CardDescription className="text-xs mt-1">
              Unsupervised dimensionality reduction of log-transformed &amp; standardized (R, F, M) metrics
            </CardDescription>
          </div>

          {/* Quick Segment Filter Pill Bar */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-muted-foreground flex items-center gap-1 text-[11px] mr-1">
              <Filter className="h-3 w-3" /> Filter:
            </span>
            <button
              onClick={() => setSelectedSegment(null)}
              className={`px-2 py-0.5 rounded-full text-[11px] transition-colors border ${
                selectedSegment === null
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-muted/50 text-muted-foreground border-border/50 hover:bg-muted"
              }`}
            >
              All ({customers.length})
            </button>
            {segments.slice(0, 5).map((s) => {
              const active = selectedSegment === s.segment;
              return (
                <button
                  key={s.segment}
                  onClick={() =>
                    setSelectedSegment(active ? null : s.segment)
                  }
                  className={`px-2 py-0.5 rounded-full text-[11px] transition-colors border ${
                    active
                      ? "text-white font-medium shadow-sm"
                      : "bg-muted/40 hover:bg-muted text-muted-foreground border-border/40"
                  }`}
                  style={{
                    backgroundColor: active ? s.color : undefined,
                    borderColor: active ? s.color : undefined,
                  }}
                >
                  {s.segment}
                </button>
              );
            })}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="h-[360px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 15, right: 20, bottom: 20, left: 0 }}>
              <XAxis
                type="number"
                dataKey="x"
                name="Principal Component 1"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11, fill: "currentColor" }}
                className="text-muted-foreground"
                label={{
                  value: `Principal Component 1 (${varianceExplained[0]}% Variance · Overall Engagement & Spend)`,
                  position: "insideBottom",
                  offset: -10,
                  fontSize: 11,
                  fill: "currentColor",
                  className: "text-muted-foreground font-medium",
                }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="Principal Component 2"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11, fill: "currentColor" }}
                className="text-muted-foreground"
                label={{
                  value: `Principal Component 2 (${varianceExplained[1]}% Variance · Frequency vs Recency)`,
                  angle: -90,
                  position: "insideLeft",
                  offset: 12,
                  fontSize: 11,
                  fill: "currentColor",
                  className: "text-muted-foreground font-medium",
                }}
              />
              <ZAxis type="number" dataKey="z" range={[40, 160]} />
              <Tooltip
                cursor={{ strokeDasharray: "3 3", stroke: "rgba(128,128,128,0.4)" }}
                content={({ active, payload }) => {
                  if (!active || !payload || !payload.length) return null;
                  const data = payload[0].payload as ScatterDataPoint;
                  const churnBadgeColor =
                    data.churnStatus === "Active"
                      ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/20"
                      : data.churnStatus === "At Risk"
                      ? "text-amber-500 bg-amber-500/10 border-amber-500/20"
                      : "text-red-500 bg-red-500/10 border-red-500/20";

                  return (
                    <div className="rounded-lg border border-border bg-popover/95 p-3 text-popover-foreground shadow-xl backdrop-blur-md text-xs min-w-[210px] space-y-2">
                      <div className="flex items-center justify-between gap-2 border-b border-border/50 pb-1.5">
                        <span className="font-semibold">{data.customerName}</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded-full border font-medium ${churnBadgeColor}`}
                        >
                          {data.churnStatus === "Active"
                            ? "🟢 Active"
                            : data.churnStatus === "At Risk"
                            ? "🟡 At Risk"
                            : "🔴 Churned"}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-muted-foreground">Cohort:</span>
                        <span
                          className="font-medium px-1.5 py-0.5 rounded text-[10px]"
                          style={{
                            color: data.color,
                            backgroundColor: `${data.color}15`,
                          }}
                        >
                          {data.segment}
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-1 pt-1 text-center bg-muted/30 rounded p-1.5 text-[10px]">
                        <div>
                          <div className="text-muted-foreground">Recency</div>
                          <div className="font-semibold text-foreground">
                            {data.recencyDays}d
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Orders</div>
                          <div className="font-semibold text-foreground">
                            {data.frequency}x
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Spend</div>
                          <div className="font-semibold text-foreground">
                            {formatInr(data.monetary)}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-1 text-[10px] text-muted-foreground border-t border-border/40">
                        <span>
                          PC1: <b className="text-foreground">{data.x}</b> · PC2:{" "}
                          <b className="text-foreground">{data.y}</b>
                        </span>
                        <span>
                          Churn Risk: <b className="text-foreground">{data.churnScore}%</b>
                        </span>
                      </div>
                    </div>
                  );
                }}
              />
              <Scatter name="Customers" data={displayedData}>
                {displayedData.map((entry, index) => (
                  <Cell
                    key={`pca-cell-${index}`}
                    fill={entry.color}
                    fillOpacity={0.7}
                    stroke={entry.color}
                    strokeWidth={1.2}
                    className="hover:opacity-100 transition-opacity cursor-pointer"
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-3 pt-3 border-t border-border/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5 text-primary shrink-0" />
            <span>
              Customer clusters naturally separate in PCA space: High-value cohorts (Champions, Loyal) cluster towards the right ($PC_1 &gt; 0$), while At Risk &amp; Churned cluster towards the left ($PC_1 &lt; 0$).
            </span>
          </div>
          {selectedSegment && (
            <button
              onClick={() => setSelectedSegment(null)}
              className="text-xs text-primary hover:underline self-start sm:self-auto shrink-0"
            >
              Reset filter
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
