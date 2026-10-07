import { NextResponse } from "next/server";
import { SEGMENT_PATTERNS } from "@/lib/rfm";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    segments: SEGMENT_PATTERNS,
  });
}
