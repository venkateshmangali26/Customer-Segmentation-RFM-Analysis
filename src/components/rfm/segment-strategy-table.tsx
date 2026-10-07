"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
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

export function SegmentStrategyTable({ segments }: Props) {
  return (
    <Card className="border-border/60">
      <CardHeader>
        <CardTitle className="text-base">Segment Summary &amp; Strategy</CardTitle>
        <CardDescription>
          Customer count, average metrics, and recommended marketing strategy per segment
        </CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px] pl-6">Segment</TableHead>
                <TableHead className="text-right">Customers</TableHead>
                <TableHead className="text-right">Revenue</TableHead>
                <TableHead className="text-right">Avg Recency</TableHead>
                <TableHead className="text-right">Avg Frequency</TableHead>
                <TableHead className="text-right">Avg Monetary</TableHead>
                <TableHead className="pl-6">Description</TableHead>
                <TableHead>Recommended Strategy</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {segments.map((s) => (
                <TableRow key={s.segment} className="align-top">
                  <TableCell className="pl-6">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: s.color }}
                      />
                      <span className="font-medium">{s.segment}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {s.count.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(s.revenue)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {s.avgRecency.toFixed(1)}d
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {s.avgFrequency.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(s.avgMonetary)}
                  </TableCell>
                  <TableCell className="pl-6">
                    <div className="text-xs text-muted-foreground max-w-[280px] whitespace-normal break-words">
                      {s.description}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs max-w-[320px] whitespace-normal break-words">
                      {s.strategy}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {segments.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                    No segments yet. Seed sample data to see results.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

export function SegmentBadges({ segments }: { segments: SegmentSummary[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {segments.map((s) => (
        <Badge
          key={s.segment}
          variant="outline"
          className="gap-1.5"
          style={{
            color: s.color,
            borderColor: `${s.color}66`,
            backgroundColor: `${s.color}12`,
          }}
        >
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: s.color }}
          />
          {s.segment}
          <span className="ml-1 tabular-nums text-muted-foreground">{s.count}</span>
        </Badge>
      ))}
    </div>
  );
}
