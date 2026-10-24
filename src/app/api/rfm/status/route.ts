import { NextResponse } from "next/server";
import { db, ensureSchema } from "@/lib/db";

// Status endpoint used by the UI to know whether the database has data yet.
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    await ensureSchema();
    const customerCount = await db.customer.count();
    const transactionCount = await db.transaction.count();
    const snapshotCount = await db.rfmSnapshot.count();
    return NextResponse.json({
      hasData: customerCount > 0 && transactionCount > 0,
      customerCount,
      transactionCount,
      snapshotCount,
    });
  } catch (err) {
    console.warn("[rfm/status] warning:", err);
    return NextResponse.json({
      hasData: false,
      customerCount: 0,
      transactionCount: 0,
      snapshotCount: 0,
    });
  }
}
