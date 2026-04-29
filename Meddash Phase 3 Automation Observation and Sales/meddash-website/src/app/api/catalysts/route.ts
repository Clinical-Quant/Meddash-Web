import { NextResponse } from "next/server";

const mockData = [
  { id: "1", ticker: "VRTX", title: "PDUFA decision window", event_type: "FDA", event_date: "2026-05-12", description: "Regulatory catalyst" },
  { id: "2", ticker: "MRNA", title: "8-K earnings guidance update", event_type: "SEC_8K", event_date: "2026-05-15", description: "Filing event" },
  { id: "3", ticker: "BNTX", title: "Phase 2 readout", event_type: "TRIAL", event_date: "2026-05-19", description: "Clinical update" },
  { id: "4", ticker: "REGN", title: "ASCO presentation", event_type: "CONFERENCE", event_date: "2026-05-23", description: "Conference catalyst" },
];

export async function GET() {
  return NextResponse.json({ data: mockData });
}
