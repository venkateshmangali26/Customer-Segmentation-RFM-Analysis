"use client";

import { useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Search } from "lucide-react";
import type { CustomerRfm, SegmentSummary } from "./types";

type Props = {
  customers: CustomerRfm[];
  segments: SegmentSummary[];
};

function formatMoney(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

type SortKey = "recencyDays" | "frequency" | "monetary" | "customerName";
type SortDir = "asc" | "desc";

function SortIndicator({
  col,
  sortKey,
  sortDir,
}: {
  col: SortKey;
  sortKey: SortKey;
  sortDir: SortDir;
}) {
  const active = sortKey === col;
  return (
    <span
      className={`ml-1 ${active ? "text-foreground" : "text-muted-foreground/40"}`}
    >
      {active ? (sortDir === "asc" ? "▲" : "▼") : "↕"}
    </span>
  );
}

export function CustomerTable({ customers, segments }: Props) {
  const [search, setSearch] = useState("");
  const [segmentFilter, setSegmentFilter] = useState("all");
  const [sortKey, setSortKey] = useState<SortKey>("monetary");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const segmentColorMap = useMemo(
    () => new Map(segments.map((s) => [s.segment, s.color])),
    [segments]
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const out = customers.filter((c) => {
      const matchesSearch =
        !q ||
        c.customerName.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        c.country.toLowerCase().includes(q);
      const matchesSegment =
        segmentFilter === "all" || c.segment === segmentFilter;
      return matchesSearch && matchesSegment;
    });
    out.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "customerName") {
        cmp = a.customerName.localeCompare(b.customerName);
      } else {
        cmp = (a[sortKey] as number) - (b[sortKey] as number);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return out;
  }, [customers, search, segmentFilter, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const paged = filtered.slice((safePage - 1) * pageSize, safePage * pageSize);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir(key === "customerName" ? "asc" : "desc");
    }
    setPage(1);
  };

  return (
    <Card className="border-border/60">
      <CardHeader>
        <CardTitle className="text-base">Customer Detail</CardTitle>
        <CardDescription>
          Browse, search, and filter customers by segment. Click a column header to sort.
        </CardDescription>
        <div className="flex flex-col sm:flex-row gap-2 mt-3">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Search by name, email, or country..."
              className="pl-8"
            />
          </div>
          <Select
            value={segmentFilter}
            onValueChange={(v) => {
              setSegmentFilter(v);
              setPage(1);
            }}
          >
            <SelectTrigger className="w-full sm:w-[200px]">
              <SelectValue placeholder="Filter by segment" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All segments</SelectItem>
              {segments.map((s) => (
                <SelectItem key={s.segment} value={s.segment}>
                  {s.segment} ({s.count})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <button
                    className="font-medium hover:text-foreground"
                    onClick={() => toggleSort("customerName")}
                  >
                    Customer<SortIndicator col="customerName" sortKey={sortKey} sortDir={sortDir} />
                  </button>
                </TableHead>
                <TableHead>Segment</TableHead>
                <TableHead>Channel</TableHead>
                <TableHead>RFM</TableHead>
                <TableHead className="text-right">
                  <button
                    className="font-medium hover:text-foreground"
                    onClick={() => toggleSort("recencyDays")}
                  >
                    Recency<SortIndicator col="recencyDays" sortKey={sortKey} sortDir={sortDir} />
                  </button>
                </TableHead>
                <TableHead className="text-right">
                  <button
                    className="font-medium hover:text-foreground"
                    onClick={() => toggleSort("frequency")}
                  >
                    Frequency<SortIndicator col="frequency" sortKey={sortKey} sortDir={sortDir} />
                  </button>
                </TableHead>
                <TableHead className="text-right">
                  <button
                    className="font-medium hover:text-foreground"
                    onClick={() => toggleSort("monetary")}
                  >
                    Monetary<SortIndicator col="monetary" sortKey={sortKey} sortDir={sortDir} />
                  </button>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paged.map((c) => {
                const color = segmentColorMap.get(c.segment) ?? "#9ca3af";
                return (
                  <TableRow key={c.customerId}>
                    <TableCell>
                      <div className="font-medium">{c.customerName}</div>
                      <div className="text-xs text-muted-foreground">{c.email}</div>
                    </TableCell>
                    <TableCell>
                      <span
                        className="inline-flex items-center gap-1.5 text-xs rounded-full px-2 py-0.5"
                        style={{
                          color: color,
                          backgroundColor: `${color}1a`,
                        }}
                      >
                        <span
                          className="h-1.5 w-1.5 rounded-full"
                          style={{ backgroundColor: color }}
                        />
                        {c.segment}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{c.channel}</TableCell>
                    <TableCell>
                      <span className="font-mono text-sm">{c.rfmScore}</span>
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {c.recencyDays}d
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{c.frequency}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(c.monetary)}
                    </TableCell>
                  </TableRow>
                );
              })}
              {paged.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="text-center text-muted-foreground py-8"
                  >
                    No customers match your filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        {filtered.length > pageSize && (
          <div className="flex items-center justify-between mt-4 text-sm">
            <div className="text-muted-foreground">
              Showing {(safePage - 1) * pageSize + 1}–
              {Math.min(safePage * pageSize, filtered.length)} of {filtered.length}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={safePage === 1}
                className="px-3 py-1 rounded-md border border-border disabled:opacity-40 hover:bg-accent"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={safePage === totalPages}
                className="px-3 py-1 rounded-md border border-border disabled:opacity-40 hover:bg-accent"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
