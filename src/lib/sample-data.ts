import { db } from "@/lib/db";

const FIRST_NAMES = [
  // Common Indian female first names
  "Aanya", "Aadhya", "Ananya", "Diya", "Kiara", "Pari", "Myra", "Anika",
  "Navya", "Aarohi", "Riya", "Sara", "Ira", "Ishita", "Aditi", "Pooja",
  "Priya", "Sneha", "Kavya", "Deepika", "Shreya", "Neha", "Tanvi", "Meera",
  "Swati", "Saanvi", "Shruti", "Anjali", "Roshni", "Sunita", "Lakshmi",
  // Common Indian male first names
  "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
  "Krishna", "Ishaan", "Rohan", "Aryan", "Rahul", "Karan", "Sameer", "Vikram",
  "Anand", "Pranav", "Nikhil", "Siddharth", "Gaurav", "Harsh", "Akash", "Manish",
  "Rajesh", "Suresh", "Ramesh", "Deepak", "Amit", "Varun", "Abhishek", "Kunal",
];

const LAST_NAMES = [
  // North India
  "Sharma", "Verma", "Gupta", "Singh", "Agarwal", "Kapoor", "Khanna", "Mishra", "Pandey", "Tiwari",
  // West India
  "Patel", "Shah", "Desai", "Mehta", "Joshi", "Patil", "Kulkarni", "Dalal", "Modi", "Pawar",
  // South India
  "Reddy", "Iyer", "Nair", "Rao", "Shetty", "Murthy", "Subramanian", "Menon", "Pillai", "Venkatesh",
  // East India
  "Banerjee", "Chatterjee", "Bhattacharya", "Mukherjee", "Das", "Ghosh", "Sengupta", "Bose", "Roy",
];

// Major Indian States & Territories by E-commerce Hubs
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

const PRODUCT_CATEGORIES = [
  "Ethnic & Contemporary Fashion",
  "Mobile & Tech Accessories",
  "Home & Kitchen Essentials",
  "Ayurveda & Wellness",
  "Beauty & Personal Care",
  "Grocery, Spices & Gourmet",
  "Festival Specials & Hampers",
  "Books, Puja & Handicrafts",
];

function randInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomEmail(name: string): string {
  const domains = ["gmail.com", "outlook.com", "yahoo.in", "rediffmail.com", "icloud.com"];
  const slug = name.toLowerCase().replace(/\s+/g, ".");
  return `${slug}${randInt(1, 9999)}@${pick(domains)}`;
}

function randomName(): string {
  return `${pick(FIRST_NAMES)} ${pick(LAST_NAMES)}`;
}

/**
 * Generates `count` customers with realistic transaction histories in INR (₹)
 * biased to produce a healthy spread across all RFM segments in the Indian market.
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

  const archetypes = allocateArchetypes(customerCount);

  for (let i = 0; i < customerCount; i++) {
    const name = randomName();
    const customer = {
      id: `cust_${i + 1}_${Math.random().toString(36).slice(2, 8)}`,
      name,
      email: randomEmail(name),
      country: pick(INDIAN_STATES),
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

  // Realistic INR (₹) ticket sizes for typical Indian D2C & marketplace shopping
  const config: Record<
    Archetype,
    { recency: [number, number]; orders: [number, number]; spend: [number, number] }
  > = {
    champion: { recency: [1, 14], orders: [8, 18], spend: [2500, 9500] },
    loyal: { recency: [15, 45], orders: [6, 12], spend: [1500, 6000] },
    potential: { recency: [5, 30], orders: [3, 6], spend: [1000, 3500] },
    new: { recency: [1, 14], orders: [1, 1], spend: [800, 3200] },
    promising: { recency: [10, 40], orders: [1, 2], spend: [700, 2400] },
    attention: { recency: [40, 90], orders: [2, 5], spend: [1200, 4000] },
    sleep: { recency: [60, 120], orders: [1, 3], spend: [600, 2000] },
    risk: { recency: [90, 180], orders: [4, 9], spend: [2000, 7500] },
    hibernating: { recency: [120, 240], orders: [1, 3], spend: [400, 1500] },
    lost: { recency: [240, 540], orders: [1, 2], spend: [300, 1100] },
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
    
    // In INR, rounded to nearest whole rupee or .00
    const rawAmount = randInt(c.spend[0], c.spend[1]);
    const amount = Number(rawAmount.toFixed(2));

    txs.push({
      id: `tx_${customerId}_${i}_${Math.random().toString(36).slice(2, 8)}`,
      customerId,
      orderId: `ORD-IN-${customerId.slice(-4)}-${i + 1}`,
      amount,
      currency: "INR",
      productCategory: pick(PRODUCT_CATEGORIES),
      occurredAt: new Date(occurredMs),
      createdAt: new Date(),
    });
  }
  return txs;
}
