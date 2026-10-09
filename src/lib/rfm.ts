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
      "Your highest-value VIP customers who purchase frequently and generate peak GMV. High festive shopping propensity and brand advocacy.",
    strategy:
      "Personalized WhatsApp VIP concierge, early preview access to Diwali & Big Billion Day flash sales, luxury festive hampers on orders over ₹4,999. Avoid margin-diluting discount codes.",
    rRange: [4, 5],
    fRange: [4, 5],
    mRange: [4, 5],
  },
  {
    segment: "Loyal",
    color: "#0ea5e9",
    description:
      "Consistent repeat shoppers with healthy basket size across key categories. Dependable backbone of recurring brand revenue.",
    strategy:
      "Cross-sell across lifestyle & grocery categories, tier-based SuperCoins loyalty rewards, free express delivery on orders above ₹799.",
    rRange: [2, 5],
    fRange: [3, 5],
    mRange: [3, 5],
  },
  {
    segment: "Potential Loyalists",
    color: "#84cc16",
    description:
      "Recent buyers with 2–3 purchases showing strong frequency momentum. High conversion potential to long-term brand advocates.",
    strategy:
      "Onboard into loyalty program, send personalized WhatsApp re-engagement codes (e.g. FESTIVE15), offer bundling discounts on complementary Indian SKUs.",
    rRange: [3, 5],
    fRange: [1, 3],
    mRange: [1, 3],
  },
  {
    segment: "New Customers",
    color: "#22d3ee",
    description:
      "First-time shoppers who made their initial purchase recently. Fresh potential requiring swift onboarding and trust building.",
    strategy:
      "Automated WhatsApp welcome series, post-delivery satisfaction survey, flat ₹200 off on second purchase within 14 days to establish habit.",
    rRange: [4, 5],
    fRange: [1, 1],
    mRange: [1, 5],
  },
  {
    segment: "Promising",
    color: "#a855f7",
    description:
      "Recent shoppers with moderate order values. Show early interest but have not yet developed a consistent buying pattern.",
    strategy:
      "Showcase bestselling regional items, announce upcoming festive sale events (Holi / Rakhi), incentivize second purchase with free shipping over ₹499.",
    rRange: [3, 4],
    fRange: [1, 2],
    mRange: [1, 2],
  },
  {
    segment: "Need Attention",
    color: "#f59e0b",
    description:
      "Above-average historical order value, but inactive for 45–90 days. Risk of drifting away to competitor marketplaces.",
    strategy:
      "Send a 'We Miss You' campaign via WhatsApp with personalized recommendations and a 15% festive comeback coupon.",
    rRange: [2, 3],
    fRange: [2, 3],
    mRange: [2, 3],
  },
  {
    segment: "About To Sleep",
    color: "#fb923c",
    description:
      "Below-average recency and frequency. At immediate risk of churn to Amazon/Flipkart/Meesho.",
    strategy:
      "Reactivate with a limited-time festive flash offer, popular high-margin trial pack, or UPI instant cashback incentive.",
    rRange: [2, 3],
    fRange: [1, 2],
    mRange: [1, 2],
  },
  {
    segment: "At Risk",
    color: "#ef4444",
    description:
      "Previously frequent high-spenders who haven't ordered in 3–6 months. Critical high-value revenue retention priority.",
    strategy:
      "High-touch retention push: direct WhatsApp & SMS outreach with an exclusive ₹500 off voucher on orders above ₹1,999.",
    rRange: [1, 2],
    fRange: [3, 5],
    mRange: [3, 5],
  },
  {
    segment: "Cannot Lose Them",
    color: "#dc2626",
    description:
      "Top historical spenders who haven't ordered in over 6 months. Losing them heavily impacts annual brand margins.",
    strategy:
      "Dedicated account manager or founder-signed outreach, VIP festival gift hamper, and deep celebratory anniversary credit.",
    rRange: [1, 1],
    fRange: [4, 5],
    mRange: [4, 5],
  },
  {
    segment: "Hibernating",
    color: "#6b7280",
    description:
      "Long recency, low order count and basket value. Low return on ad spend for sustained acquisition.",
    strategy:
      "Low-cost mass WhatsApp / SMS broadcast during major annual festivals (Diwali / New Year); avoid expensive paid retargeting.",
    rRange: [1, 2],
    fRange: [1, 2],
    mRange: [1, 2],
  },
  {
    segment: "Lost",
    color: "#9ca3af",
    description:
      "Zero activity for over 8–18 months. Completely churned from the brand ecosystem.",
    strategy:
      "Suppress from regular paid ad spend; utilize strictly for anonymous lookalike audience creation in Meta & Google Ads.",
    rRange: [1, 1],
    fRange: [1, 1],
    mRange: [1, 1],
  },
  {
    segment: "Average Customers",
    color: "#64748b",
    description:
      "Moderate recency, frequency, and order values without a decisive pattern across categories.",
    strategy:
      "Nudge into specific category journeys with curated seasonal recommendations to boost AOV beyond ₹1,500.",
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
