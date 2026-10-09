"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Loader2 } from "lucide-react";
import { toast } from "sonner";

const INDIAN_STATES = [
  "Maharashtra",
  "Karnataka",
  "Delhi NCR",
  "Tamil Nadu",
  "Telangana",
  "Gujarat",
  "Uttar Pradesh",
  "West Bengal",
  "Rajasthan",
  "Kerala",
  "Punjab",
  "Haryana",
  "Madhya Pradesh",
  "Andhra Pradesh",
  "Bihar",
];

const CHANNELS = [
  "WhatsApp Store",
  "Mobile App",
  "Web Store",
  "Amazon.in / Flipkart",
  "Quick Commerce",
  "Retail Outlet",
];

const CATEGORIES = [
  "Ethnic & Contemporary Fashion",
  "Mobile & Tech Accessories",
  "Home & Kitchen Essentials",
  "Ayurveda & Wellness",
  "Beauty & Personal Care",
  "Grocery, Spices & Gourmet",
  "Festival Specials & Hampers",
  "Books, Puja & Handicrafts",
];

type Props = {
  onCreated: () => void;
};

export function AddTransactionDialog({ onCreated }: Props) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    customerName: "",
    email: "",
    country: "Maharashtra",
    channel: "WhatsApp Store",
    orderId: "",
    amount: "",
    productCategory: "Ethnic & Contemporary Fashion",
    occurredAt: new Date().toISOString().slice(0, 10),
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.customerName || !form.email || !form.orderId || !form.amount) {
      toast.error("Please fill in customer name, email, order ID, and amount");
      return;
    }
    const amountNum = parseFloat(form.amount);
    if (Number.isNaN(amountNum) || amountNum <= 0) {
      toast.error("Amount must be a positive number in INR (₹)");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customerName: form.customerName,
          email: form.email,
          country: form.country,
          channel: form.channel,
          orderId: form.orderId,
          amount: amountNum,
          productCategory: form.productCategory,
          occurredAt: new Date(form.occurredAt).toISOString(),
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Request failed" }));
        throw new Error(err.error || "Failed to create transaction");
      }
      toast.success("Transaction recorded and RFM recomputed in INR");
      setOpen(false);
      setForm({
        customerName: "",
        email: "",
        country: "Maharashtra",
        channel: "WhatsApp Store",
        orderId: "",
        amount: "",
        productCategory: "Ethnic & Contemporary Fashion",
        occurredAt: new Date().toISOString().slice(0, 10),
      });
      onCreated();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to add transaction");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default" size="sm" className="gap-1.5 shadow-sm">
          <Plus className="h-4 w-4" />
          Add Transaction
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>Record Order Transaction (INR ₹)</DialogTitle>
          <DialogDescription>
            Record a new customer order. If the customer exists (matched by email), their metrics update automatically and RFM scores re-calculate.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="customerName">Customer Name</Label>
              <Input
                id="customerName"
                value={form.customerName}
                onChange={(e) => setForm({ ...form, customerName: e.target.value })}
                placeholder="Aarav Sharma"
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="aarav.sharma@gmail.com"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="country">State / Region (India)</Label>
              <Select
                value={form.country}
                onValueChange={(v) => setForm({ ...form, country: v })}
              >
                <SelectTrigger id="country">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {INDIAN_STATES.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="channel">Sales Channel</Label>
              <Select
                value={form.channel}
                onValueChange={(v) => setForm({ ...form, channel: v })}
              >
                <SelectTrigger id="channel">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CHANNELS.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="orderId">Order ID</Label>
              <Input
                id="orderId"
                value={form.orderId}
                onChange={(e) => setForm({ ...form, orderId: e.target.value })}
                placeholder="ORD-IN-1092"
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="amount">Amount (INR ₹)</Label>
              <Input
                id="amount"
                type="number"
                step="1"
                min="1"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                placeholder="2499"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="category">Product Category</Label>
              <Select
                value={form.productCategory}
                onValueChange={(v) => setForm({ ...form, productCategory: v })}
              >
                <SelectTrigger id="category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="occurredAt">Purchase Date</Label>
              <Input
                id="occurredAt"
                type="date"
                value={form.occurredAt}
                onChange={(e) => setForm({ ...form, occurredAt: e.target.value })}
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Save &amp; Recompute RFM
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
