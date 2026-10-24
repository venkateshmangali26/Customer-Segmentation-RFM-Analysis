import { PrismaClient } from "@prisma/client";
import path from "path";
import fs from "fs";
import os from "os";

function resolveDatabaseUrl(): string {
  const envUrl = process.env.DATABASE_URL;

  // If user configured a remote cloud database (e.g. Postgres, Neon, Turso), use it directly
  if (envUrl && !envUrl.startsWith("file:")) {
    return envUrl;
  }

  // Running on Vercel / AWS Lambda serverless (root filesystem is read-only for SQLite)
  if (process.env.VERCEL || process.env.AWS_LAMBDA_FUNCTION_NAME) {
    const tmpDir = os.tmpdir();
    const tmpDbPath = path.join(tmpDir, "custom.db");
    if (!fs.existsSync(tmpDbPath)) {
      const sourceDb = path.join(process.cwd(), "db", "custom.db");
      if (fs.existsSync(sourceDb)) {
        try {
          fs.copyFileSync(sourceDb, tmpDbPath);
        } catch (err) {
          console.warn("[db] Could not copy custom.db to tmp:", err);
        }
      }
    }
    const vercelUrl = `file:${tmpDbPath.replace(/\\/g, "/")}`;
    process.env.DATABASE_URL = vercelUrl;
    return vercelUrl;
  }

  if (envUrl) {
    return envUrl;
  }

  // Local fallback
  const localDb = path.join(process.cwd(), "db", "custom.db");
  const localUrl = `file:${localDb}`;
  process.env.DATABASE_URL = localUrl;
  return localUrl;
}

const resolvedUrl = resolveDatabaseUrl();

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const db =
  globalForPrisma.prisma ??
  new PrismaClient({
    datasources: {
      db: {
        url: resolvedUrl,
      },
    },
    log: process.env.NODE_ENV === "development" ? ["warn", "error"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = db;

const DDL_STATEMENTS = [
  `CREATE TABLE IF NOT EXISTS "Customer" (
      "id" TEXT NOT NULL PRIMARY KEY,
      "name" TEXT NOT NULL,
      "email" TEXT NOT NULL,
      "country" TEXT NOT NULL DEFAULT 'India',
      "channel" TEXT NOT NULL DEFAULT 'Web Store',
      "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      "updatedAt" DATETIME NOT NULL
  )`,
  `CREATE TABLE IF NOT EXISTS "Transaction" (
      "id" TEXT NOT NULL PRIMARY KEY,
      "customerId" TEXT NOT NULL,
      "orderId" TEXT NOT NULL,
      "amount" REAL NOT NULL,
      "currency" TEXT NOT NULL DEFAULT 'INR',
      "productCategory" TEXT,
      "occurredAt" DATETIME NOT NULL,
      "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT "Transaction_customerId_fkey" FOREIGN KEY ("customerId") REFERENCES "Customer" ("id") ON DELETE CASCADE ON UPDATE CASCADE
  )`,
  `CREATE TABLE IF NOT EXISTS "RfmSnapshot" (
      "id" TEXT NOT NULL PRIMARY KEY,
      "customerId" TEXT NOT NULL,
      "recencyDays" INTEGER NOT NULL,
      "frequency" INTEGER NOT NULL,
      "monetary" REAL NOT NULL,
      "recencyScore" INTEGER NOT NULL,
      "frequencyScore" INTEGER NOT NULL,
      "monetaryScore" INTEGER NOT NULL,
      "rfmScore" TEXT NOT NULL,
      "segment" TEXT NOT NULL,
      "updatedAt" DATETIME NOT NULL,
      CONSTRAINT "RfmSnapshot_customerId_fkey" FOREIGN KEY ("customerId") REFERENCES "Customer" ("id") ON DELETE CASCADE ON UPDATE CASCADE
  )`,
  `CREATE UNIQUE INDEX IF NOT EXISTS "Customer_email_key" ON "Customer"("email")`,
  `CREATE INDEX IF NOT EXISTS "Transaction_customerId_idx" ON "Transaction"("customerId")`,
  `CREATE INDEX IF NOT EXISTS "Transaction_occurredAt_idx" ON "Transaction"("occurredAt")`,
  `CREATE UNIQUE INDEX IF NOT EXISTS "RfmSnapshot_customerId_key" ON "RfmSnapshot"("customerId")`,
  `CREATE INDEX IF NOT EXISTS "RfmSnapshot_segment_idx" ON "RfmSnapshot"("segment")`,
];

let schemaEnsured = false;

/**
 * Ensures SQLite tables and indexes exist even on fresh serverless container instances.
 */
export async function ensureSchema() {
  if (schemaEnsured) return;
  for (const sql of DDL_STATEMENTS) {
    try {
      await db.$executeRawUnsafe(sql);
    } catch {
      // Table or index already exists
    }
  }
  schemaEnsured = true;
}