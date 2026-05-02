import { NextResponse } from "next/server";

export const runtime = "edge";

export async function GET() {
  return NextResponse.json({
    data: [],
    notice: "No live catalyst source connected yet. Mock data intentionally removed.",
  });
}
