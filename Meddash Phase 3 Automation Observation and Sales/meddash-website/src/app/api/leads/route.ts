import { NextRequest, NextResponse } from "next/server";

export const runtime = "edge";

export async function POST(req: NextRequest) {
  const body = await req.json();
  if (!body?.email) {
    return NextResponse.json({ error: "email is required" }, { status: 400 });
  }

  // Temporary success response; wire to Supabase in B.2.x
  return NextResponse.json({ ok: true, received: body });
}
