"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Sparkles,
  Loader2,
  RefreshCw,
  Database,
  Activity,
  PieChart,
  Table2,
  Users,
  Plus,
} from "lucide-react";
import { toast } from "sonner";

import type { RfmAnalysisResponse } from "@/components/rfm/types";
import { StatCards } from "@/components/rfm/stat-cards";
import { SegmentDonut } from "@/components/rfm/segment-donut";
import { ScoreDistributionChart } from "@/components/rfm/score-distribution";
import { RfmBubbleChart } from "@/components/rfm/rfm-bubble";
import {
  SegmentStrategyTable,
  SegmentBadges,
} from "@/components/rfm/segment-strategy-table";
import { CustomerTable } from "@/components/rfm/customer-table";
import { AddTransactionDialog } from "@/components/rfm/add-transaction-dialog";
import { EmptyState } from "@/components/rfm/empty-state";

export default function Home() {
  const [data, setData] = useState<RfmAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [hasData, setHasData] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch("/api/rfm/analyze", { cache: "no-store" });
      if (!res.ok) throw new Error("Failed to load RFM analysis");
      const json: RfmAnalysisResponse = await res.json();
      setData(json);
      setHasData(json.totalCustomers > 0);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const recompute = async () => {
    setRecomputing(true);
    try {
      const res = await fetch("/api/rfm/analyze", { cache: "no-store" });
      if (!res.ok) throw new Error("Recompute failed");
      const json: RfmAnalysisResponse = await res.json();
      setData(json);
      toast.success("RFM analysis refreshed");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Refresh failed");
    } finally {
      setRecomputing(false);
    }
  };

  const seedSample = async () => {
    setSeeding(true);
    try {
      const res = await fetch("/api/rfm/seed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count: 220 }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Seeding failed" }));
        throw new Error(err.error || "Seeding failed");
      }
      const result = await res.json();
      toast.success(
        `Seeded ${result.seeded.customers} customers and ${result.seeded.transactions} transactions`
      );
      await fetchData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Seeding failed");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-background to-muted/30">
      {/* Sticky header */}
      <header className="sticky top-0 z-30 border-b border-border/60 bg-background/80 backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-primary flex items-center justify-center">
              <Activity className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold leading-tight">
                  Customer Segmentation — RFM Analysis
                </h1>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  India Edition (₹)
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-tight">
                Recency × Frequency × Monetary Scoring · Indian Retail &amp; D2C Metrics
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={recompute}
              disabled={recomputing || !hasData}
            >
              {recomputing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={seedSample}
              disabled={seeding}
            >
              {seeding ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Database className="h-4 w-4" />
              )}
              Seed India Demo (₹)
            </Button>
            <AddTransactionDialog onCreated={fetchData} />
          </div>
        </div>
      </header>

      <main className="flex-1 mx-auto max-w-7xl w-full px-4 sm:px-6 lg:px-8 py-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading RFM analysis…</p>
          </div>
        ) : !hasData || !data || data.totalCustomers === 0 ? (
          <EmptyState onSeeded={fetchData} />
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            {/* KPI row */}
            <StatCards
              totalCustomers={data.totalCustomers}
              totalRevenue={data.totalRevenue}
              totalTransactions={data.totalTransactions}
              avgOrderValue={data.avgOrderValue}
            />

            {/* Tabs */}
            <Tabs defaultValue="dashboard" className="w-full">
              <TabsList className="grid w-full grid-cols-3 max-w-md">
                <TabsTrigger value="dashboard" className="gap-1.5">
                  <PieChart className="h-3.5 w-3.5" />
                  Dashboard
                </TabsTrigger>
                <TabsTrigger value="segments" className="gap-1.5">
                  <Users className="h-3.5 w-3.5" />
                  Segments
                </TabsTrigger>
                <TabsTrigger value="customers" className="gap-1.5">
                  <Table2 className="h-3.5 w-3.5" />
                  Customers
                </TabsTrigger>
              </TabsList>

              <TabsContent value="dashboard" className="mt-4 space-y-6">
                <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
                  <SegmentDonut segments={data.segmentSummary} />
                  <ScoreDistributionChart distribution={data.scoreDistribution} />
                </div>
                <RfmBubbleChart
                  customers={data.customers}
                  segments={data.segmentSummary}
                />
                <SegmentBadges segments={data.segmentSummary} />
              </TabsContent>

              <TabsContent value="segments" className="mt-4">
                <SegmentStrategyTable segments={data.segmentSummary} />
              </TabsContent>

              <TabsContent value="customers" className="mt-4">
                <CustomerTable
                  customers={data.customers}
                  segments={data.segmentSummary}
                />
              </TabsContent>
            </Tabs>
          </motion.div>
        )}
      </main>

      {/* Sticky footer */}
      <footer className="mt-auto border-t border-border/60 bg-background/60">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5" />
            <span>
              RFM segmentation based on{" "}
              <span className="font-medium text-foreground">{data?.totalCustomers ?? 0}</span>{" "}
              customers · Reference date:{" "}
              <span className="font-medium text-foreground">
                {data ? new Date(data.referenceDate).toLocaleDateString() : "—"}
              </span>
            </span>
          </div>
          <div>
            Quantile scoring 1–5 per axis · 11 behavioral segments · Calibrated for Indian e-commerce &amp; D2C in INR (₹)
          </div>
        </div>
      </footer>
    </div>
  );
}
