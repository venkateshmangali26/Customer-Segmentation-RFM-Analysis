import { NextResponse } from "next/server";
import { runRfmAnalysis, summarizeBySegment } from "@/lib/rfm";
import { ensureSchema } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    await ensureSchema();
    const result = await runRfmAnalysis();
    const segmentSummary = summarizeBySegment(result.customers);
    const totalRevenue = result.customers.reduce((s, c) => s + c.monetary, 0);
    const totalTx = result.customers.reduce((s, c) => s + c.frequency, 0);
    const avgOrderValue = totalTx > 0 ? totalRevenue / totalTx : 0;

    // Per-axis distribution for charts
    const scoreDistribution = {
      r: [0, 0, 0, 0, 0],
      f: [0, 0, 0, 0, 0],
      m: [0, 0, 0, 0, 0],
    };
    const churnBreakdown = {
      active: 0,
      atRisk: 0,
      churned: 0,
    };
    for (const c of result.customers) {
      scoreDistribution.r[c.recencyScore - 1] += 1;
      scoreDistribution.f[c.frequencyScore - 1] += 1;
      scoreDistribution.m[c.monetaryScore - 1] += 1;

      if (c.churnStatus === "Active") churnBreakdown.active += 1;
      else if (c.churnStatus === "At Risk") churnBreakdown.atRisk += 1;
      else churnBreakdown.churned += 1;
    }

    return NextResponse.json({
      referenceDate: result.referenceDate,
      totalCustomers: result.totalCustomers,
      totalRevenue: Number(totalRevenue.toFixed(2)),
      avgOrderValue: Number(avgOrderValue.toFixed(2)),
      totalTransactions: totalTx,
      segmentSummary,
      scoreDistribution,
      customers: result.customers,
      pcaVariance: result.pcaVariance,
      churnBreakdown,
    });
  } catch (err) {
    console.error("[rfm/analyze] error:", err);
    return NextResponse.json(
      { error: "Failed to run RFM analysis", detail: String(err) },
      { status: 500 }
    );
  }
}
