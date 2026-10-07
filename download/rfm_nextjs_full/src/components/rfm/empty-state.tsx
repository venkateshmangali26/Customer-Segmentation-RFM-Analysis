"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Loader2, Database } from "lucide-react";
import { toast } from "sonner";

type Props = {
  onSeeded: () => void;
};

export function EmptyState({ onSeeded }: Props) {
  const [loading, setLoading] = useState(false);

  const seed = async () => {
    setLoading(true);
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
      const data = await res.json();
      toast.success(
        `Seeded ${data.seeded.customers} customers and ${data.seeded.transactions} transactions`
      );
      onSeeded();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Seeding failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <Card className="max-w-lg w-full border-border/60 text-center">
        <CardHeader>
          <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-2">
            <Database className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-xl">Welcome to RFM Analysis</CardTitle>
          <CardDescription className="text-sm">
            There are no transactions in your database yet. To explore the dashboard,
            either seed the demo dataset (220 realistic customers across 10 countries)
            or add your first transaction manually.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button onClick={seed} disabled={loading} className="w-full sm:w-auto">
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {loading ? "Generating..." : "Seed sample dataset"}
          </Button>
          <p className="text-xs text-muted-foreground">
            The sample dataset includes customers, transaction histories across up to 2 years,
            and a representative spread across all 11 RFM segments so you can explore the
            full segmentation immediately.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
