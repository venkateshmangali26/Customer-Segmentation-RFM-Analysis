import { db } from "@/lib/db";

// ---------------------------------------------------------------------------
// RFM segment definitions
// Each segment is identified by an RFM score pattern. Scores use:
//   5 = top tier (e.g. very recent, very frequent, very high monetary)
//   1 = bottom tier
// Patterns use ranges like "4-5" or "*" (wildcard = any).
// Order matters: the first matching segment wins.
// ---------------------------------------------------------------------------

export type RfmPattern = {
  segment: string;
  color: string;
  description: string;
  strategy: string;
  rRange: [number, number];
  fRange: [number, number];
  mRange: [number, number];
};

export const SEGMENT_PATTERNS: RfmPattern[] = [
  {
    segment: "Champions",
    color: "#10b981",
    description:
      "Your best customers — bought recently, buy often, and spend the most. They are brand advocates who can drive referrals.",
    strategy:
      "Reward them with exclusive perks, early access to new products, and a referral program. Avoid heavy discounting — they would buy anyway.",
    rRange: [4, 5],
    fRange: [4, 5],
    mRange: [4, 5],
  },
  {
    segment: "Loyal",
    color: "#0ea5e9",
    description:
      "Consistent repeat purchasers with strong monetary value. Reliable revenue base that responds well to upselling.",
    strategy:
      "Upsell higher-margin products, bundle complementary items, and offer a loyalty program with tier-based rewards.",
    rRange: [2, 5],
    fRange: [3, 5],
    mRange: [3, 5],
  },
  {
    segment: "Potential Loyalists",
    color: "#84cc16",
    description:
      "Recent customers with above-average frequency. They are still forming habits and deciding whether to commit to your brand.",
    strategy:
      "Onboard them into a loyalty program, send personalized re-engagement offers, and ask for reviews to deepen their investment.",
    rRange: [3, 5],
    fRange: [1, 3],
    mRange: [1, 3],
  },
  {
    segment: "New Customers",
    color: "#22d3ee",
    description:
      "Brand new customers who just made their first purchase. High potential but still unproven.",
    strategy:
      "Send a welcome series with onboarding content, a small discount on the next purchase, and a satisfaction check-in.",
    rRange: [4, 5],
    fRange: [1, 1],
    mRange: [1, 5],
  },
  {
    segment: "Promising",
    color: "#a855f7",
    description:
      "Recent buyers with average spend. Showing early signs of engagement but not yet frequent.",
    strategy:
      "Build brand affinity through content marketing, recommend products similar to their first purchase, and introduce a loyalty program.",
    rRange: [3, 4],
    fRange: [1, 2],
    mRange: [1, 2],
  },
  {
    segment: "Need Attention",
    color: "#f59e0b",
    description:
      "Above-average recency and frequency, but haven't purchased recently. The window to re-engage is closing.",
    strategy:
      "Send a personalized offer or a 'we miss you' campaign. Highlight new products and limited-time perks to bring them back.",
    rRange: [2, 3],
    fRange: [2, 3],
    mRange: [2, 3],
  },
  {
    segment: "About To Sleep",
    color: "#fb923c",
    description:
      "Below-average recency and frequency. They are drifting away from your brand and need a nudge before they churn.",
    strategy:
      "Reactivate with a time-sensitive discount, a free shipping offer, or a personalized product recommendation.",
    rRange: [2, 3],
    fRange: [1, 2],
    mRange: [1, 2],
  },
  {
    segment: "At Risk",
    color: "#ef4444",
    description:
      "Used to buy often and spend a lot, but haven't purchased in a while. High-value customers you must win back.",
    strategy:
      "Send a 'we want you back' campaign with a meaningful incentive. Personalize based on their past purchases and ask for feedback.",
    rRange: [1, 2],
    fRange: [3, 5],
    mRange: [3, 5],
  },
  {
    segment: "Cannot Lose Them",
    color: "#dc2626",
    description:
      "High spenders who haven't purchased in a long time. Losing them would mean losing significant future revenue.",
    strategy:
      "Reach out personally with a high-value offer, a renewal of their loyalty benefits, or an exclusive invitation to a VIP event.",
    rRange: [1, 1],
    fRange: [4, 5],
    mRange: [4, 5],
  },
  {
    segment: "Hibernating",
    color: "#6b7280",
    description:
      "Low recency, frequency, and monetary. Inactive customers who haven't engaged in a long time.",
    strategy:
      "Send a final re-engagement campaign. If they don't respond, suppress them from regular email lists to protect deliverability.",
    rRange: [1, 2],
    fRange: [1, 2],
    mRange: [1, 2],
  },
  {
    segment: "Lost",
    color: "#9ca3af",
    description:
      "Lowest scores across all dimensions. They are effectively churned.",
    strategy:
      "Use them for lookalike audiences in paid acquisition, or send a single reactivation campaign. Don't waste budget on sustained outreach.",
    rRange: [1, 1],
    fRange: [1, 1],
    mRange: [1, 1],
  },
  {
    segment: "Average Customers",
    color: "#64748b",
    description:
      "Customers who don't fit a clear archetype — middling recency, frequency, and monetary value. They represent the broad middle of your customer base.",
    strategy:
      "Monitor closely. Move them into a targeted segment with a single relevant offer or product recommendation to push them toward a clearer pattern.",
    rRange: [1, 5],
    fRange: [1, 5],
    mRange: [1, 5],
  },
];

export type RfmScore = {
  r: number;
  f: number;
  m: number;
};

export type CustomerRfm = {
  customerId: string;
  customerName: string;
  email: string;
  country: string;
  channel: string;
  recencyDays: number;
  frequency: number;
  monetary: number;
  recencyScore: number;
  frequencyScore: number;
  monetaryScore: number;
  rfmScore: string;
  segment: string;
};

/**
 * Score a value from 1 to 5 using quantile thresholds.
 * `ascending=true` means a higher raw value → higher score (Frequency, Monetary).
 * `ascending=false` means a lower raw value → higher score (Recency).
 */
function scoreQuantile(
  value: number,
  thresholds: { q20: number; q40: number; q60: number; q80: number },
  ascending: boolean
): number {
  // For ascending metrics, higher raw value = higher score
  // For descending metrics (recency), lower raw value = higher score
  const t = thresholds;
  if (ascending) {
    if (value <= t.q20) return 1;
    if (value <= t.q40) return 2;
    if (value <= t.q60) return 3;
    if (value <= t.q80) return 4;
    return 5;
  } else {
    // For recency: lower is better
    // thresholds are computed on the raw distribution, so we invert comparisons
    if (value <= t.q20) return 5;
    if (value <= t.q40) return 4;
    if (value <= t.q60) return 3;
    if (value <= t.q80) return 2;
    return 1;
  }
}

function quantile(sorted: number[], q: number): number {
  if (sorted.length === 0) return 0;
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  }
  return sorted[base];
}

/**
 * Compute the segment for a given (R, F, M) score combination.
 * Falls back to "Average Customers" if no specific pattern matches.
 */
export function classifySegment(r: number, f: number, m: number): string {
  for (const pattern of SEGMENT_PATTERNS) {
    const inR = r >= pattern.rRange[0] && r <= pattern.rRange[1];
    const inF = f >= pattern.fRange[0] && f <= pattern.fRange[1];
    const inM = m >= pattern.mRange[0] && m <= pattern.mRange[1];
    if (inR && inF && inM) return pattern.segment;
  }
  // Catch-all fallback (always defined as last pattern)
  return "Average Customers";
}

/**
 * Run the full RFM pipeline:
 * 1. Aggregate per-customer metrics from transactions.
 * 2. Compute quantile thresholds for R, F, M.
 * 3. Score each customer 1-5 on each axis.
 * 4. Classify into a segment.
 * 5. Persist the result as an RfmSnapshot.
 */
export async function runRfmAnalysis(referenceDate?: Date): Promise<{
  referenceDate: string;
  totalCustomers: number;
  totalRevenue: number;
  segments: CustomerRfm[];
  customers: CustomerRfm[];
}> {
  const refDate = referenceDate ?? new Date();
  // Use a stable date string for comparison purposes
  const refTime = refDate.getTime();

  const transactions = await db.transaction.findMany({
    include: { customer: true },
    orderBy: { occurredAt: "asc" },
  });

  if (transactions.length === 0) {
    return {
      referenceDate: refDate.toISOString(),
      totalCustomers: 0,
      totalRevenue: 0,
      segments: [],
      customers: [],
    };
  }

  // Step 1: per-customer aggregation
  const perCustomer = new Map<
    string,
    {
      customer: { id: string; name: string; email: string; country: string; channel: string };
      lastPurchaseAt: number;
      orderIds: Set<string>;
      totalSpend: number;
    }
  >();

  let totalRevenue = 0;
  for (const tx of transactions) {
    const existing = perCustomer.get(tx.customerId);
    const occurredMs = tx.occurredAt.getTime();
    if (existing) {
      if (occurredMs > existing.lastPurchaseAt) {
        existing.lastPurchaseAt = occurredMs;
      }
      existing.orderIds.add(tx.orderId);
      existing.totalSpend += tx.amount;
    } else {
      perCustomer.set(tx.customerId, {
        customer: {
          id: tx.customer.id,
          name: tx.customer.name,
          email: tx.customer.email,
          country: tx.customer.country,
          channel: tx.customer.channel,
        },
        lastPurchaseAt: occurredMs,
        orderIds: new Set([tx.orderId]),
        totalSpend: tx.amount,
      });
    }
    totalRevenue += tx.amount;
  }

  const customerMetrics = Array.from(perCustomer.entries()).map(([id, data]) => ({
    customerId: id,
    customer: data.customer,
    recencyDays: Math.max(
      0,
      Math.floor((refTime - data.lastPurchaseAt) / (1000 * 60 * 60 * 24))
    ),
    frequency: data.orderIds.size,
    monetary: data.totalSpend,
  }));

  // Step 2: compute quantiles
  const sortedRecency = customerMetrics.map((c) => c.recencyDays).sort((a, b) => a - b);
  const sortedFrequency = customerMetrics.map((c) => c.frequency).sort((a, b) => a - b);
  const sortedMonetary = customerMetrics.map((c) => c.monetary).sort((a, b) => a - b);

  const recencyThresholds = {
    q20: quantile(sortedRecency, 0.2),
    q40: quantile(sortedRecency, 0.4),
    q60: quantile(sortedRecency, 0.6),
    q80: quantile(sortedRecency, 0.8),
  };
  const frequencyThresholds = {
    q20: quantile(sortedFrequency, 0.2),
    q40: quantile(sortedFrequency, 0.4),
    q60: quantile(sortedFrequency, 0.6),
    q80: quantile(sortedFrequency, 0.8),
  };
  const monetaryThresholds = {
    q20: quantile(sortedMonetary, 0.2),
    q40: quantile(sortedMonetary, 0.4),
    q60: quantile(sortedMonetary, 0.6),
    q80: quantile(sortedMonetary, 0.8),
  };

  // Step 3 & 4: score and classify
  const result: CustomerRfm[] = customerMetrics.map((c) => {
    const rScore = scoreQuantile(c.recencyDays, recencyThresholds, false);
    const fScore = scoreQuantile(c.frequency, frequencyThresholds, true);
    const mScore = scoreQuantile(c.monetary, monetaryThresholds, true);
    const segment = classifySegment(rScore, fScore, mScore);
    return {
      customerId: c.customerId,
      customerName: c.customer.name,
      email: c.customer.email,
      country: c.customer.country,
      channel: c.customer.channel,
      recencyDays: c.recencyDays,
      frequency: c.frequency,
      monetary: c.monetary,
      recencyScore: rScore,
      frequencyScore: fScore,
      monetaryScore: mScore,
      rfmScore: `${rScore}${fScore}${mScore}`,
      segment,
    };
  });

  // Step 5: persist
  await db.$transaction(
    result.map((r) =>
      db.rfmSnapshot.upsert({
        where: { customerId: r.customerId },
        create: {
          customerId: r.customerId,
          recencyDays: r.recencyDays,
          frequency: r.frequency,
          monetary: r.monetary,
          recencyScore: r.recencyScore,
          frequencyScore: r.frequencyScore,
          monetaryScore: r.monetaryScore,
          rfmScore: r.rfmScore,
          segment: r.segment,
        },
        update: {
          recencyDays: r.recencyDays,
          frequency: r.frequency,
          monetary: r.monetary,
          recencyScore: r.recencyScore,
          frequencyScore: r.frequencyScore,
          monetaryScore: r.monetaryScore,
          rfmScore: r.rfmScore,
          segment: r.segment,
        },
      })
    )
  );

  return {
    referenceDate: refDate.toISOString(),
    totalCustomers: result.length,
    totalRevenue,
    segments: result,
    customers: result,
  };
}

/**
 * Aggregate RFM snapshots into segment-level summary.
 */
export function summarizeBySegment(customers: CustomerRfm[]) {
  const map = new Map<
    string,
    {
      segment: string;
      count: number;
      revenue: number;
      avgRecency: number;
      avgFrequency: number;
      avgMonetary: number;
    }
  >();
  for (const c of customers) {
    const ex = map.get(c.segment) ?? {
      segment: c.segment,
      count: 0,
      revenue: 0,
      avgRecency: 0,
      avgFrequency: 0,
      avgMonetary: 0,
    };
    ex.count += 1;
    ex.revenue += c.monetary;
    ex.avgRecency += c.recencyDays;
    ex.avgFrequency += c.frequency;
    ex.avgMonetary += c.monetary;
    map.set(c.segment, ex);
  }
  const arr = Array.from(map.values());
  for (const a of arr) {
    a.avgRecency = a.count > 0 ? a.avgRecency / a.count : 0;
    a.avgFrequency = a.count > 0 ? a.avgFrequency / a.count : 0;
    a.avgMonetary = a.count > 0 ? a.avgMonetary / a.count : 0;
  }
  // attach pattern metadata (color, description, strategy)
  return arr
    .map((a) => {
      const pattern = SEGMENT_PATTERNS.find((p) => p.segment === a.segment);
      return {
        ...a,
        color: pattern?.color ?? "#9ca3af",
        description: pattern?.description ?? "",
        strategy: pattern?.strategy ?? "",
      };
    })
    .sort((a, b) => b.count - a.count);
}
