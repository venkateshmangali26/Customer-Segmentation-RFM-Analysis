// Shared client-side types for RFM dashboard components

export type ChurnStatus = "Active" | "At Risk" | "Churned";

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
  churnStatus: ChurnStatus;
  churnScore: number;
  pc1?: number;
  pc2?: number;
};

export type SegmentSummary = {
  segment: string;
  count: number;
  revenue: number;
  avgRecency: number;
  avgFrequency: number;
  avgMonetary: number;
  color: string;
  description: string;
  strategy: string;
};

export type ScoreDistribution = {
  r: number[];
  f: number[];
  m: number[];
};

export type RfmAnalysisResponse = {
  referenceDate: string;
  totalCustomers: number;
  totalRevenue: number;
  avgOrderValue: number;
  totalTransactions: number;
  segmentSummary: SegmentSummary[];
  scoreDistribution: ScoreDistribution;
  customers: CustomerRfm[];
  pcaVariance?: [number, number];
  churnBreakdown?: {
    active: number;
    atRisk: number;
    churned: number;
  };
};
