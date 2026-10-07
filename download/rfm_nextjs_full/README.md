# Customer Segmentation RFM Analysis — Next.js Web App

Interactive customer-segmentation dashboard built with **Next.js 16 + TypeScript + Prisma + SQLite + Recharts + shadcn/ui**.

This is the **frontend + backend web application** version of the RFM analysis project (as opposed to the Python/Streamlit version). It runs as a single full-stack Next.js app: the API routes do the RFM computation server-side, and the React dashboard renders the results client-side.

---

## 📁 Project layout (47 files)

```
rfm_nextjs_full/
├── README.md                   ← you are here
├── .env.example                ← copy to .env, edit DATABASE_URL
├── .gitignore
│
├── package.json                ← dependencies + scripts
├── tsconfig.json
├── next.config.ts
├── tailwind.config.ts
├── postcss.config.mjs
├── eslint.config.mjs
├── components.json             ← shadcn/ui config
│
├── prisma/
│   └── schema.prisma           ← Customer, Transaction, RfmSnapshot models
│
├── public/
│   ├── logo.svg
│   └── robots.txt
│
└── src/
    ├── app/
    │   ├── layout.tsx          ← root layout + Sonner toaster
    │   ├── page.tsx            ← main dashboard (sticky header, tabs, sticky footer)
    │   ├── globals.css         ← Tailwind v4 + theme tokens (light/dark)
    │   └── api/                ← BACKEND API ROUTES
    │       ├── rfm/
    │       │   ├── analyze/route.ts    ← GET: runs full RFM pipeline, returns KPIs + segments + customers
    │       │   ├── seed/route.ts       ← POST: generates 220-customer demo dataset
    │       │   ├── segments/route.ts   ← GET: returns segment pattern metadata
    │       │   └── status/route.ts     ← GET: returns DB population status
    │       ├── transactions/route.ts  ← GET: list 200 recent txns  |  POST: add a txn + recompute RFM
    │       └── customers/route.ts      ← GET: list 500 customers w/ their latest segment
    │
    ├── lib/
    │   ├── db.ts                ← singleton PrismaClient
    │   ├── rfm.ts               ← RFM ENGINE: quantile scoring + 12 segment patterns
    │   ├── sample-data.ts       ← 220-customer realistic demo data generator (10 archetypes)
    │   └── utils.ts             ← cn() class merger (clsx + tailwind-merge)
    │
    ├── hooks/
    │   ├── use-toast.ts         ← legacy toast hook
    │   └── use-mobile.ts        ← viewport breakpoint hook
    │
    └── components/
        ├── rfm/                 ← DASHBOARD-SPECIFIC COMPONENTS
        │   ├── types.ts                       ← shared TS types
        │   ├── stat-cards.tsx                  ← 4 KPI cards (animated entry)
        │   ├── segment-donut.tsx               ← donut chart of segment distribution
        │   ├── score-distribution.tsx          ← grouped bar chart (R/F/M × score 1..5)
        │   ├── rfm-bubble.tsx                  ← R×F×M bubble scatter, colored by segment
        │   ├── segment-strategy-table.tsx      ← 12-row segment table + badges
        │   ├── customer-table.tsx              ← sortable / filterable / paginated table
        │   ├── add-transaction-dialog.tsx      ← form dialog: add a transaction
        │   └── empty-state.tsx                 ← onboarding card with one-click seed
        │
        └── ui/                  ← SHADCN/UI PRIMITIVES (13 components used)
            ├── badge.tsx, button.tsx, card.tsx, dialog.tsx,
            │   dropdown-menu.tsx, form.tsx, input.tsx, label.tsx,
            │   popover.tsx, select.tsx, separator.tsx, sonner.tsx,
            │   table.tsx, tabs.tsx, toast.tsx, toaster.tsx, tooltip.tsx
```

> **Note**: Only the shadcn/ui components actually used by the dashboard are included. The original `components.json` references the full shadcn registry; if you need more components (calendar, command, accordion, etc.), install them via `npx shadcn@latest add <name>`.

---

## 🚀 Quickstart

```bash
# 1. Install dependencies (Node 18+ required)
npm install            # or: bun install / pnpm install / yarn install

# 2. Copy the env file and configure DATABASE_URL
cp .env.example .env
# Edit .env — the default is "file:./db/custom.db" (SQLite, no extra setup)

# 3. Push the Prisma schema to the database
npx prisma db push
# This creates the SQLite file and generates the Prisma Client

# 4. Run the dev server
npm run dev
# Open http://localhost:3000

# 5. First run: click "Seed demo" in the top-right of the dashboard
#    This generates 220 customers with ~900 transactions across 11 segments
```

### One-time Prisma setup (alternative)

```bash
# Generate Prisma Client without pushing schema
npx prisma generate

# Push schema and accept data-loss warnings (safe on first run)
npx prisma db push --accept-data-loss

# Reset DB if needed
npx prisma migrate reset
```

---

## 🧪 What the app does

### The dashboard (single page, 3 tabs)

| Tab | What you see |
|-----|--------------|
| **Dashboard** | 4 KPI cards (Total Customers / Revenue / Transactions / Avg Order Value) + donut chart of segment distribution + grouped bar chart of R/F/M score distribution (1–5) + R×F×M bubble scatter colored by segment (bubble size = total spend) + segment count badges |
| **Segments** | Full table of 12 segment patterns with: customer count, total revenue, avg recency/frequency/monetary, segment description, and recommended marketing strategy per segment |
| **Customers** | Searchable + filterable + sortable + paginated customer table. Filter by segment, sort by name/recency/frequency/monetary. 25 rows per page. |

### Top-right actions

- **Refresh** — re-runs the RFM pipeline (`GET /api/rfm/analyze`)
- **Seed demo** — generates 220 customers with realistic transaction histories biased across 10 archetypes (`POST /api/rfm/seed`)
- **Add Transaction** — opens a form dialog. On submit, the API upserts the customer by email (idempotent), prevents duplicate Order IDs, and **recomputes the entire RFM pipeline live** (`POST /api/transactions`)

### Empty state

When the DB is empty, the dashboard shows an onboarding card with a "Seed sample dataset" button — one click and you're looking at the populated dashboard.

---

## 🔌 API reference

All routes are under `/api/*`. They return JSON.

### `GET /api/rfm/analyze`
Runs the full RFM pipeline server-side and returns everything the dashboard needs in one call.

```jsonc
{
  "referenceDate": "2026-10-07T10:00:00.000Z",
  "totalCustomers": 220,
  "totalRevenue": 149900.50,
  "avgOrderValue": 158.92,
  "totalTransactions": 943,
  "segmentSummary": [
    { "segment": "Champions", "count": 18, "revenue": 42000, "avgRecency": 5.2, "avgFrequency": 12.4, "avgMonetary": 2333.33, "color": "#10b981", "description": "...", "strategy": "..." },
    ...
  ],
  "scoreDistribution": {
    "r": [10, 25, 50, 75, 60],   // count of customers at each R score 1..5
    "f": [60, 75, 50, 25, 10],
    "m": [40, 35, 45, 50, 50]
  },
  "customers": [ /* full customer list with RFM scores + segment */ ]
}
```

### `POST /api/rfm/seed`
Generates a realistic demo dataset. Optional body: `{ "count": 220 }` (10–2000).

```jsonc
{
  "ok": true,
  "seeded": { "customers": 220, "transactions": 909 },
  "totalCustomers": 220,
  "totalRevenue": 149900.50
}
```

### `GET /api/rfm/segments`
Returns the 12 segment pattern definitions (color, description, strategy, R/F/M ranges).

### `GET /api/rfm/status`
Returns DB population status. Used by the dashboard to decide whether to show the empty state.

```jsonc
{ "hasData": true, "customerCount": 220, "transactionCount": 909, "snapshotCount": 220 }
```

### `POST /api/transactions`
Adds a transaction. If the email exists, the customer is updated; otherwise a new customer is created. Duplicate `(customerId, orderId)` pairs are rejected (409). After insert, RFM is recomputed and persisted.

Request body:
```jsonc
{
  "customerName": "Jane Doe",
  "email": "jane@example.com",
  "country": "United States",
  "channel": "Web",
  "orderId": "ORD-12345",
  "amount": 129.99,
  "productCategory": "Electronics",
  "occurredAt": "2026-10-07T10:00:00.000Z"
}
```

### `GET /api/transactions`
Returns the 200 most recent transactions with customer info joined.

### `GET /api/customers`
Returns 500 customers with their latest segment and RFM score.

---

## 🧮 The RFM engine (`src/lib/rfm.ts`)

The engine runs in 5 steps server-side:

1. **Aggregate** — for each customer, compute:
   - `Recency` = days since last purchase
   - `Frequency` = distinct order count
   - `Monetary` = total spend

2. **Quantile thresholds** — for each axis, compute the 20/40/60/80th percentiles across all customers.

3. **Score 1–5** — assign a quantile score per axis:
   - Recency: lower days → higher score (5 = most recent)
   - Frequency & Monetary: higher values → higher score

4. **Classify segment** — match the (R,F,M) triple against 12 segment patterns:
   - Champions, Loyal, Potential Loyalists, New Customers, Promising,
   - Need Attention, About To Sleep, At Risk, Cannot Lose Them,
   - Hibernating, Lost, **Average Customers** (catch-all)

5. **Persist** — upsert each customer's `RfmSnapshot` row (their latest R/F/M scores + segment). This makes subsequent queries cheap.

Each segment has a `color`, `description`, and actionable `strategy` baked into the pattern table — so the dashboard's segment table renders automatically.

---

## 🎨 Frontend architecture

- **State**: each tab fetches from `/api/rfm/analyze` on mount. No client-side store needed — `fetch` + `useState` is enough.
- **Charts**: [Recharts](https://recharts.org) for the donut, bar, and bubble charts. Bubble chart is a `ScatterChart` with one `<Scatter>` series per segment for color coding, plus a `<ZAxis>` to encode monetary value as bubble size.
- **Tables**: shadcn/ui `Table` primitives + custom sort/filter/pagination logic in `customer-table.tsx`.
- **Forms**: `react-hook-form` + `zod` for validation in `add-transaction-dialog.tsx`.
- **Toasts**: `sonner` (rich, closeable, top-right).
- **Animations**: `framer-motion` for KPI card entrance + page fade-in.
- **Responsive**: mobile-first. KPI grid collapses 4→2→1 columns. Tables scroll horizontally on narrow screens. Custom legend below the bubble chart wraps gracefully.

### Theme

- Tailwind v4 with `@theme inline` mapping CSS variables to Tailwind colors.
- Light + dark tokens defined in `globals.css` (dark mode wiring is via `next-themes` if you want to add a toggle).
- Segment colors come from the backend pattern table (`SEGMENT_PATTERNS` in `rfm.ts`), so they stay consistent across all charts.

---

## 🛠️ Tech stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Framework | Next.js 16 (App Router) | One codebase for API + UI |
| Language | TypeScript 5 (strict) | |
| Styling | Tailwind CSS v4 + shadcn/ui (New York style) | Pre-built components in `src/components/ui/` |
| Database | Prisma + SQLite | Zero-config; file-based at `db/custom.db` |
| Charts | Recharts | Donut, bar, scatter |
| Forms | react-hook-form + zod | Used in add-transaction dialog |
| Toasts | sonner + Radix toast | Sonner is the primary UX |
| Animations | framer-motion | KPI card entrance, page fade |
| Icons | lucide-react | |
| Date utils | date-fns | |

---

## ✅ Quality checks

The project lints cleanly:

```bash
npm run lint    # 0 errors, 0 warnings
```

End-to-end browser-verified (using `agent-browser`) for:
- Empty state onboarding
- Seed demo flow
- Dashboard tab (donut + bar + bubble + badges)
- Segments tab (full strategy table, no truncation)
- Customers tab (search, filter, sort, pagination)
- Add Transaction dialog (form validation, customer upsert, live RFM recompute)
- Mobile viewport (375px): vertical stacking, no horizontal overflow
- Sticky footer on short pages, pushed down on long pages

---

## 🧭 Suggested next steps

- **CSV upload** — replace the "Seed demo" button with a CSV upload for real transaction data.
- **Date range filter** — recompute RFM for a custom window (e.g. last 90 days).
- **Export segment lists** — add a "Download CSV" button per segment in the Customers tab.
- **Dark mode toggle** — the theme tokens already support it; just add a `next-themes` switcher in the header.
- **Custom segment rules** — let users tweak the R/F/M pattern thresholds in `SEGMENT_PATTERNS`.
- **WebSocket updates** — if multiple users add transactions concurrently, broadcast segment changes via Socket.IO.
