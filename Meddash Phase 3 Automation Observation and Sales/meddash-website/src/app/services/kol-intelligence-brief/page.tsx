import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "KOL Intelligence Brief | Meddash.ai",
  description:
    "KOL identification platform support for biotech teams: 72-hour decision-ready brief with therapeutic context and action priorities.",
  alternates: { canonical: "https://meddash.ai/services/kol-intelligence-brief" },
};

export default function KolIntelligenceBriefPage() {
  return (
    <main className="min-h-screen bg-background text-foreground px-6 md:px-10 py-16">
      <section className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-semibold text-white">KOL Intelligence Brief</h1>
        <p className="mt-4 text-slate-300">
          Our KOL identification platform workflow helps biotech teams prioritize relevant experts fast, with decision-ready context in 72 hours.
        </p>
        <ul className="mt-6 list-disc list-inside text-slate-200 space-y-2">
          <li>Therapeutic-area specific KOL map and ranking rationale</li>
          <li>Publication, trial, and speaking signal consolidation</li>
          <li>Action plan for immediate outreach windows</li>
        </ul>
        <a href="/#lead?utm_source=service&utm_medium=kol-brief" className="inline-block mt-8 rounded-lg bg-meddash-cyan text-black font-semibold px-5 py-3">
          Request Brief
        </a>
      </section>
    </main>
  );
}
