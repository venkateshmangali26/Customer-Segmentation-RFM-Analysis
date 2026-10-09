# Customer Segmentation - RFM Intelligence Platform (India Edition)

A production-grade Recency x Frequency x Monetary (RFM) analytics platform built for the Indian retail & D2C ecosystem. Segments customers into 11 behavioral cohorts and reports all metrics in Indian Rupees with Lakhs & Crores formatting.

![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![React](https://img.shields.io/badge/React-19-blue?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Prisma](https://img.shields.io/badge/Prisma-ORM-2D3748?logo=prisma)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- 11 customer segments tuned for Indian retail (Champions, Loyal, Potential Loyalists, New Customers, Promising, Need Attention, About To Sleep, At Risk, Cannot Lose Them, Hibernating, Lost)
- Quantile-based RFM scoring (1-5 scale per dimension)
- Indian currency formatting with Lakhs (L) and Crores (Cr) compact notation
- Full Prisma ORM schema: Customer, Transaction, RfmSnapshot
- API routes: /api/rfm/analyze, /api/rfm/seed, /api/rfm/transaction
- Visualizations: StatCards, SegmentDonut, ScoreDistribution, RfmBubble, CustomerTable
- Framer Motion animations, Sonner toasts, shadcn/ui components

## Tech Stack

- Next.js 15 (App Router)
- React 19, Tailwind CSS, shadcn/ui
- Recharts, Framer Motion, Sonner
- Prisma ORM, SQLite (dev) / PostgreSQL (prod)
- TypeScript 5

## Getting Started

1. Clone the repo
2. npm install
3. Create .env with DATABASE_URL="file:./dev.db"
4. npx prisma generate && npx prisma db push
5. npm run dev

## Author

**Venkatesh Mangali** - [GitHub](https://github.com/venkateshmangali26)

## License

MIT License
