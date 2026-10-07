"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, DollarSign, ShoppingBag, Receipt } from "lucide-react";
import { motion } from "framer-motion";

type Props = {
  totalCustomers: number;
  totalRevenue: number;
  totalTransactions: number;
  avgOrderValue: number;
};

function formatMoney(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(2)}`;
}

function StatCard({
  label,
  value,
  icon: Icon,
  accent,
  hint,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  accent: string;
  hint: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="relative overflow-hidden border-border/60">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {label}
          </CardTitle>
          <div
            className="h-9 w-9 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${accent}1a`, color: accent }}
          >
            <Icon className="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-semibold tabular-nums">{value}</div>
          <p className="text-xs text-muted-foreground mt-1">{hint}</p>
        </CardContent>
        <div
          className="absolute left-0 top-0 h-full w-1"
          style={{ backgroundColor: accent }}
        />
      </Card>
    </motion.div>
  );
}

export function StatCards({
  totalCustomers,
  totalRevenue,
  totalTransactions,
  avgOrderValue,
}: Props) {
  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Total Customers"
        value={totalCustomers.toLocaleString()}
        icon={Users}
        accent="#10b981"
        hint="Unique customers with at least one transaction"
      />
      <StatCard
        label="Total Revenue"
        value={formatMoney(totalRevenue)}
        icon={DollarSign}
        accent="#0ea5e9"
        hint="Sum of all transaction amounts"
      />
      <StatCard
        label="Total Transactions"
        value={totalTransactions.toLocaleString()}
        icon={Receipt}
        accent="#a855f7"
        hint="Distinct orders placed"
      />
      <StatCard
        label="Avg Order Value"
        value={formatMoney(avgOrderValue)}
        icon={ShoppingBag}
        accent="#f59e0b"
        hint="Total revenue divided by total transactions"
      />
    </div>
  );
}
