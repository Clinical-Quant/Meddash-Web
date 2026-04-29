"use client";

import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import { useEffect, useMemo, useState } from "react";

type Catalyst = {
  id: string;
  ticker: string;
  title: string;
  event_type: "FDA" | "SEC_8K" | "TRIAL" | "CONFERENCE";
  event_date: string;
  description?: string;
};

const COLORS: Record<Catalyst["event_type"], string> = {
  FDA: "#ef4444",
  SEC_8K: "#22c55e",
  TRIAL: "#3b82f6",
  CONFERENCE: "#f59e0b",
};

export default function CatalystCalendarSection() {
  const [events, setEvents] = useState<Catalyst[]>([]);

  useEffect(() => {
    fetch("/api/catalysts")
      .then((r) => r.json())
      .then((d) => setEvents(d?.data ?? []))
      .catch(() => setEvents([]));
  }, []);

  const mapped = useMemo(
    () =>
      events.map((e) => ({
        id: e.id,
        title: `${e.ticker} — ${e.title}`,
        start: e.event_date,
        backgroundColor: COLORS[e.event_type],
        borderColor: COLORS[e.event_type],
        extendedProps: e,
      })),
    [events]
  );

  return (
    <section id="calendar" className="px-6 md:px-10 py-16 bg-meddash-surface">
      <h2 className="text-3xl font-semibold text-white mb-3">Biotech Catalyst Calendar</h2>
      <p className="text-slate-300 mb-6">Track FDA decisions, SEC filings, trial updates, and conference events.</p>
      <div className="rounded-2xl border border-white/10 bg-[#0a1220] p-4 text-white">
        <FullCalendar
          plugins={[dayGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          events={mapped}
          height="auto"
          eventClick={(arg) => {
            const e = arg.event.extendedProps as Catalyst;
            alert(`${e.ticker} | ${e.event_type}\n${e.title}\n${e.description ?? ""}`);
          }}
        />
      </div>
    </section>
  );
}
