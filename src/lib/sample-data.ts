import { db } from "@/lib/db";

const FIRST_NAMES = [
  "Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Mason",
  "Isabella", "Lucas", "Mia", "Oliver", "Amelia", "Elijah", "Harper",
  "James", "Evelyn", "Benjamin", "Abigail", "Henry", "Emily", "Alexander",
  "Grace", "Daniel", "Chloe", "Matthew", "Victoria", "Jackson", "Aria",
  "Samuel", "Luna", "David", "Layla", "Joseph", "Zoe", "Carter", "Nora",
  "Owen", "Lily", "Wyatt", "Hannah", "John", "Eleanor", "Luke", "Stella",
  "Julian", "Mila", "Levi", "Aubrey",
];

const LAST_NAMES = [
  "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
  "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
  "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
  "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
  "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
  "Adams", "Nelson", "Baker", "Hughes", "Carter", "Mitchell", "Roberts",
];

const COUNTRIES = [
  "United States", "United Kingdom", "Canada", "Australia", "Germany",
  "France", "Japan", "Brazil", "India", "Singapore",
];

const CHANNELS = ["Web", "Mobile App", "Retail Store", "Email Campaign", "Marketplace"];

const PRODUCT_CATEGORIES = [
  "Electronics", "Apparel", "Home & Kitchen", "Beauty", "Books",
  "Sports", "Toys", "Grocery", "Office", "Garden",
];

function randInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomEmail(name: string): string {
  const domains = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "protonmail.com"];
  const slug = name.toLowerCase().replace(/\s+/g, ".");
  return `${slug}${randInt(1, 9999)}@${pick(domains)}`;
}

function randomName(): string {
  return `${pick(FIRST_NAMES)} ${pick(LAST_NAMES)}`;
}

/**
 * Generates `count` customers with realistic transaction histories
 * biased to produce a healthy spread across all RFM segments.
 *
 * The generator deliberately shapes the distribution:
 * - 10% Champion-like (frequent, recent, high spend)
 * - 15% Loyal (frequent, mid-recency, good spend)
 * - 15% At-Risk (used to buy often, but long recency)
 * - 25% New / Promising / Potential Loyalists (recent, low frequency)
 * - 20% Need Attention / About to Sleep (mid recency, low frequency)
 * - 15% Hibernating / Lost (long recency, low frequency and monetary)
 */
export async function seedSampleData(customerCount = 220): Promise<{
  customers: number;
  transactions: number;
}> {
  // Clear existing data
  await db.rfmSnapshot.deleteMany();
  await db.transaction.deleteMany();
  await db.customer.deleteMany();

  const now = Date.now();
  const dayMs = 24 * 60 * 60 * 1000;
  const customers = [];
  const transactions = [];

  // Pre-assign a behavioral archetype to each customer so the resulting
  // RFM distribution looks realistic instead of uniform random.
  const archetypes = allocateArchetypes(customerCount);

  for (let i = 0; i < customerCount; i++) {
    const name = randomName();
    const customer = {
      id: `cust_${i + 1}_${Math.random().toString(36).slice(2, 8)}`,
      name,
      email: randomEmail(name),
      country: pick(COUNTRIES),
      channel: pick(CHANNELS),
      createdAt: new Date(now - randInt(30, 720) * dayMs),
      updatedAt: new Date(),
    };
    customers.push(customer);

    const archetype = archetypes[i];
    const txs = generateTransactionsForArchetype(archetype, now, dayMs, customer.id);
    transactions.push(...txs);
  }

  // Bulk insert customers
  for (const c of customers) {
    await db.customer.create({ data: c });
  }
  // Bulk insert transactions
  for (const t of transactions) {
    await db.transaction.create({ data: t });
  }

  return {
    customers: customers.length,
    transactions: transactions.length,
  };
}

type Archetype =
  | "champion"
  | "loyal"
  | "potential"
  | "new"
  | "promising"
  | "attention"
  | "sleep"
  | "risk"
  | "hibernating"
  | "lost";

function allocateArchetypes(count: number): Archetype[] {
  const buckets: { type: Archetype; ratio: number }[] = [
    { type: "champion", ratio: 0.08 },
    { type: "loyal", ratio: 0.12 },
    { type: "potential", ratio: 0.1 },
    { type: "new", ratio: 0.1 },
    { type: "promising", ratio: 0.1 },
    { type: "attention", ratio: 0.1 },
    { type: "sleep", ratio: 0.1 },
    { type: "risk", ratio: 0.1 },
    { type: "hibernating", ratio: 0.12 },
    { type: "lost", ratio: 0.08 },
  ];
  const result: Archetype[] = [];
  for (const b of buckets) {
    const n = Math.round(count * b.ratio);
    for (let i = 0; i < n; i++) result.push(b.type);
  }
  while (result.length < count) result.push("lost");
  // Shuffle so segments interleave in the customer list
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

function generateTransactionsForArchetype(
  type: Archetype,
  now: number,
  dayMs: number,
  customerId: string
) {
  const txs: Array<{
    id: string;
    customerId: string;
    orderId: string;
    amount: number;
    currency: string;
    productCategory: string;
    occurredAt: Date;
    createdAt: Date;
  }> = [];

  const config: Record<
    Archetype,
    { recency: [number, number]; orders: [number, number]; spend: [number, number] }
  > = {
    champion: { recency: [1, 14], orders: [8, 18], spend: [120, 400] },
    loyal: { recency: [15, 45], orders: [6, 12], spend: [80, 250] },
    potential: { recency: [5, 30], orders: [3, 6], spend: [40, 120] },
    new: { recency: [1, 14], orders: [1, 1], spend: [40, 200] },
    promising: { recency: [10, 40], orders: [1, 2], spend: [30, 80] },
    attention: { recency: [40, 90], orders: [2, 5], spend: [50, 150] },
    sleep: { recency: [60, 120], orders: [1, 3], spend: [20, 80] },
    risk: { recency: [90, 180], orders: [4, 9], spend: [100, 350] },
    hibernating: { recency: [120, 240], orders: [1, 3], spend: [15, 70] },
    lost: { recency: [240, 540], orders: [1, 2], spend: [10, 50] },
  };

  const c = config[type];
  const orderCount = randInt(c.orders[0], c.orders[1]);
  const latestRecency = randInt(c.recency[0], c.recency[1]);
  const latestAt = now - latestRecency * dayMs;

  for (let i = 0; i < orderCount; i++) {
    // Spread orders backward from latestAt
    const offset = i === 0 ? 0 : randInt(15, 90) * i + randInt(5, 30);
    const occurredMs = latestAt - offset * dayMs;
    if (occurredMs < now - 365 * 2 * dayMs) continue; // keep within 2 years
    const amount = +(randInt(c.spend[0] * 10, c.spend[1] * 10) / 10).toFixed(2);
    txs.push({
      id: `tx_${customerId}_${i}_${Math.random().toString(36).slice(2, 8)}`,
      customerId,
      orderId: `ORD-${customerId.slice(-4)}-${i + 1}`,
      amount,
      currency: "USD",
      productCategory: pick(PRODUCT_CATEGORIES),
      occurredAt: new Date(occurredMs),
      createdAt: new Date(),
    });
  }
  return txs;
}
