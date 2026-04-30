import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Catalyst Interpretation | Meddash.ai",
  description:
    "Clinical trial intelligence and catalyst interpretation for biotech teams, with impact framing for cross-functional decision making.",
  alternates: { canonical: "https://meddash.ai/services/catalyst-interpretation" },
};

export default function CatalystInterpretationPage() {
  return (
    <main className="min-h-screen bg-background text-foreground px-6 md:px-10 py-16">
      <section className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-semibold text-white">Catalyst Interpretation</h1>
        <p className="mt-4 text-slate-300">
          We turn clinical trial intelligence, FDA milestones, and company updates into clear impact narratives your team can act on.
        </p>
        <ul className="mt-6 list-disc list-inside text-slate-200 space-y-2">
          <li>Event significance scoring and risk framing</li>
          <li>Competitive timing context and response options</li>
          <li>Decision memo format for internal alignment</li>
        </ul>
        <a href="/#lead?utm_source=service&utm_medium=catalyst" className="inline-block mt-8 rounded-lg bg-meddash-cyan text-black font-semibold px-5 py-3">
          Request Brief
        </a>
      </section>
    </main>
  );
}
