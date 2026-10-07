import { NextResponse } from "next/server";
import { seedSampleData } from "@/lib/sample-data";
import { runRfmAnalysis } from "@/lib/rfm";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    let count = 220;
    try {
      const body = await request.json();
      if (typeof body?.count === "number") {
        count = Math.min(2000, Math.max(10, body.count));
      }
    } catch {
      // no body is fine
    }
    const seeded = await seedSampleData(count);
    // immediately recompute RFM so the dashboard is consistent
    const analysis = await runRfmAnalysis();
    return NextResponse.json({
      ok: true,
      seeded,
      totalCustomers: analysis.totalCustomers,
      totalRevenue: Number(
        analysis.customers.reduce((s, c) => s + c.monetary, 0).toFixed(2)
      ),
    });
  } catch (err) {
    console.error("[rfm/seed] error:", err);
    return NextResponse.json(
      { error: "Failed to seed sample data", detail: String(err) },
      { status: 500 }
    );
  }
}
