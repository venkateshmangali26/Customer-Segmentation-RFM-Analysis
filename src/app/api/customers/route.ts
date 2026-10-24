import { NextResponse } from "next/server";
import { db, ensureSchema } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    await ensureSchema();
    const customers = await db.customer.findMany({
      orderBy: { createdAt: "desc" },
      take: 500,
      include: { rfm: true },
    });
    return NextResponse.json({
      customers: customers.map((c) => ({
        id: c.id,
        name: c.name,
        email: c.email,
        country: c.country,
        channel: c.channel,
        createdAt: c.createdAt.toISOString(),
        segment: c.rfm?.segment ?? null,
        rfmScore: c.rfm?.rfmScore ?? null,
      })),
    });
  } catch (err) {
    console.warn("[customers] warning:", err);
    return NextResponse.json({ customers: [] });
  }
}
