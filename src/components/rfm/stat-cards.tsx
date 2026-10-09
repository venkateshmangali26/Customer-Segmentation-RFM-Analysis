"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, IndianRupee, ShoppingBag, Receipt } from "lucide-react";
import { motion } from "framer-motion";
import { formatInr } from "@/lib/format";

type Props = {
  totalCustomers: number;
  totalRevenue: number;
  totalTransactions: number;
  avgOrderValue: number;
};

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
        value={totalCustomers.toLocaleString("en-IN")}
        icon={Users}
        accent="#10b981"
        hint="Active customers across Indian states"
      />
      <StatCard
        label="Total Revenue (INR)"
        value={formatInr(totalRevenue, true)}
        icon={IndianRupee}
        accent="#0ea5e9"
        hint="Gross sales volume in Indian Rupees"
      />
      <StatCard
        label="Total Orders"
        value={totalTransactions.toLocaleString("en-IN")}
        icon={Receipt}
        accent="#a855f7"
        hint="Fulfilled orders across all channels"
      />
      <StatCard
        label="Average Order Value"
        value={formatInr(avgOrderValue, false)}
        icon={ShoppingBag}
        accent="#f59e0b"
        hint="Average basket size per checkout"
      />
    </div>
  );
}
