Customer Segmentation - RFM Intelligence Platform (India Edition)
🚀 LIVE DEMO: https://customer-segmentation-rfm-analysis-nine.vercel.app

A production-grade Recency x Frequency x Monetary (RFM) analytics platform built for the Indian retail & D2C ecosystem. Segments customers into 11 behavioral cohorts and reports all metrics in Indian Rupees with Lakhs & Crores formatting.

Next.jsReactTypeScriptPrismaVercelLicense

Live Dashboard
Try the live demo: customer-segmentation-rfm-analysis-nine.vercel.app

The dashboard segments customers into 11 behavioral cohorts and surfaces actionable marketing strategies tuned for Indian retail (Diwali, Holi, Big Billion Day, UPI cashback, WhatsApp-first engagement).

Features
11 customer segments tuned for Indian retail (Champions, Loyal, Potential Loyalists, New Customers, Promising, Need Attention, About To Sleep, At Risk, Cannot Lose Them, Hibernating, Lost)
Quantile-based RFM scoring (1-5 scale per dimension)
Indian currency formatting with Lakhs (L) and Crores (Cr) compact notation
Full Prisma ORM schema: Customer, Transaction, RfmSnapshot
API routes: /api/rfm/analyze, /api/rfm/seed, /api/rfm/transaction
Visualizations: StatCards, SegmentDonut, ScoreDistribution, RfmBubble, CustomerTable
Framer Motion animations, Sonner toasts, shadcn/ui components
Tech Stack
Next.js 15 (App Router)
React 19, Tailwind CSS, shadcn/ui
Recharts, Framer Motion, Sonner
Prisma ORM, SQLite (dev) / PostgreSQL (prod)
TypeScript 5
Deployed on Vercel
Getting Started
Clone the repo
npm install
Create .env with DATABASE_URL="file:./dev.db"
npx prisma generate && npx prisma db push
npm run dev
Author
Venkatesh Mangali - GitHub

License
MIT License
