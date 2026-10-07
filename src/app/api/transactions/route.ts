import { NextResponse } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { runRfmAnalysis } from "@/lib/rfm";

export const dynamic = "force-dynamic";

const TransactionSchema = z.object({
  customerName: z.string().min(1).max(120),
  email: z.string().email(),
  country: z.string().optional(),
  channel: z.string().optional(),
  orderId: z.string().min(1).max(60),
  amount: z.number().positive(),
  productCategory: z.string().optional(),
  // ISO string or Date
  occurredAt: z.string().or(z.date()),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const parsed = TransactionSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: "Invalid payload", detail: parsed.error.flatten() },
        { status: 400 }
      );
    }
    const data = parsed.data;

    // Upsert customer by email
    const customer = await db.customer.upsert({
      where: { email: data.email.toLowerCase() },
      create: {
        name: data.customerName,
        email: data.email.toLowerCase(),
        country: data.country ?? "Unknown",
        channel: data.channel ?? "Manual Entry",
      },
      update: {
        name: data.customerName,
        country: data.country ?? undefined,
        channel: data.channel ?? undefined,
      },
    });

    // Check orderId is unique per customer
    const existing = await db.transaction.findFirst({
      where: { customerId: customer.id, orderId: data.orderId },
    });
    if (existing) {
      return NextResponse.json(
        { error: `Order ${data.orderId} already exists for this customer` },
        { status: 409 }
      );
    }

    const occurredAt =
      typeof data.occurredAt === "string" ? new Date(data.occurredAt) : data.occurredAt;

    await db.transaction.create({
      data: {
        customerId: customer.id,
        orderId: data.orderId,
        amount: Number(data.amount.toFixed(2)),
        currency: "USD",
        productCategory: data.productCategory ?? null,
        occurredAt,
      },
    });

    // Recompute RFM so the new transaction is reflected immediately
    await runRfmAnalysis();

    return NextResponse.json({ ok: true, customerId: customer.id });
  } catch (err) {
    console.error("[transactions] error:", err);
    return NextResponse.json(
      { error: "Failed to create transaction", detail: String(err) },
      { status: 500 }
    );
  }
}

export async function GET() {
  const txs = await db.transaction.findMany({
    include: { customer: true },
    orderBy: { occurredAt: "desc" },
    take: 200,
  });
  return NextResponse.json({
    transactions: txs.map((t) => ({
      id: t.id,
      customerId: t.customerId,
      customerName: t.customer.name,
      email: t.customer.email,
      orderId: t.orderId,
      amount: t.amount,
      currency: t.currency,
      productCategory: t.productCategory,
      occurredAt: t.occurredAt.toISOString(),
    })),
  });
}
